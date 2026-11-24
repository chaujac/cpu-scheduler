<?php
// backend/scheduler.php - pure scheduling engine + validation (no HTML, no HTTP here)

// One simulated process. "burst" never changes; "remaining" counts down while running.
class Process {
    public $pid, $arrival, $burst, $remaining, $order;
    public $completion = 0, $turnaround = 0, $waiting = 0;
    public function __construct(string $pid, int $arrival, int $burst, int $order) {
        $this->pid = $pid; $this->arrival = $arrival; $this->burst = $burst;
        $this->remaining = $burst;   // working copy used by Round Robin
        $this->order = $order;       // original input position (tie-breaks + restoring order)
    }
    // TAT = CT - AT ; WT = TAT - BT
    public function computeMetrics(): void {
        $this->turnaround = $this->completion - $this->arrival;
        $this->waiting    = $this->turnaround - $this->burst;
    }
    public function toArray(): array {
        return ['pid' => $this->pid, 'arrival' => $this->arrival, 'burst' => $this->burst,
                'completion' => $this->completion, 'turnaround' => $this->turnaround, 'waiting' => $this->waiting];
    }
}

class Scheduler {
    private array $procs;      // Process objects in ORIGINAL input order
    private array $gantt = []; // list of ['pid','start','end'] blocks
    private int $time = 0;     // simulated clock (currentTime)

    // ---------- Validation: returns a list of error strings (empty = valid) ----------
    public static function validate(array $data): array {
        $errors = [];
        $algo = $data['algorithm'] ?? '';
        if (!in_array($algo, ['FCFS', 'SJF', 'RR'], true)) $errors[] = 'Choose a valid algorithm (FCFS, SJF or RR).';
        $list = $data['processes'] ?? null;
        if (!is_array($list) || count($list) === 0) { $errors[] = 'Add at least one process.'; return $errors; }
        $seen = [];
        foreach (array_values($list) as $i => $p) {
            $n = $i + 1;
            $pid = trim((string)($p['pid'] ?? ''));
            if ($pid === '') $errors[] = "Row $n: PID cannot be empty.";
            elseif (isset($seen[$pid])) $errors[] = "Row $n: PID \"$pid\" is duplicated.";
            $seen[$pid] = true;
            $at = filter_var($p['arrival'] ?? null, FILTER_VALIDATE_INT);
            $bt = filter_var($p['burst'] ?? null, FILTER_VALIDATE_INT);
            if ($at === false) $errors[] = "Row $n: Arrival time must be a whole number.";
            elseif ($at < 0)   $errors[] = "Row $n: Arrival time cannot be negative.";
            if ($bt === false) $errors[] = "Row $n: Burst time must be a whole number.";
            elseif ($bt <= 0)  $errors[] = "Row $n: Burst time must be greater than 0.";
        }
        if ($algo === 'RR') {
            $tq = filter_var($data['quantum'] ?? null, FILTER_VALIDATE_INT);
            if ($tq === false || $tq <= 0) $errors[] = 'Time quantum must be a whole number greater than 0.';
        }
        return $errors;
    }

    public function __construct(array $rows) {
        $this->procs = [];
        foreach (array_values($rows) as $i => $r)
            $this->procs[] = new Process(trim($r['pid']), (int)$r['arrival'], (int)$r['burst'], $i);
    }

    // Sort helper: arrival ascending, ties by original order
    private function byArrival(array $list): array {
        usort($list, fn($a, $b) => [$a->arrival, $a->order] <=> [$b->arrival, $b->order]);
        return $list;
    }
    // Append a Gantt block (used for both processes and IDLE)
    private function addBlock(string $pid, int $start, int $end): void {
        $this->gantt[] = ['pid' => $pid, 'start' => $start, 'end' => $end];
    }

    // ---------- FCFS (non-preemptive) ----------
    private function fcfs(): void {
        foreach ($this->byArrival($this->procs) as $p) {
            if ($this->time < $p->arrival) {                    // CPU idle until this process arrives
                $this->addBlock('IDLE', $this->time, $p->arrival);
                $this->time = $p->arrival;                      // fast-forward the clock
            }
            $this->addBlock($p->pid, $this->time, $this->time + $p->burst);
            $this->time += $p->burst;
            $p->completion = $this->time;
        }
    }

    // ---------- SJF (non-preemptive) ----------
    private function sjf(): void {
        $left = $this->procs;                                   // processes not yet finished
        while ($left) {
            // Ready set = arrived processes
            $ready = array_values(array_filter($left, fn($p) => $p->arrival <= $this->time));
            if (!$ready) {                                      // nobody arrived: idle to the earliest arrival
                $next = min(array_map(fn($p) => $p->arrival, $left));
                $this->addBlock('IDLE', $this->time, $next);
                $this->time = $next;
                continue;
            }
            // Pick smallest burst; ties -> earlier arrival -> original order
            usort($ready, fn($a, $b) => [$a->burst, $a->arrival, $a->order] <=> [$b->burst, $b->arrival, $b->order]);
            $p = $ready[0];
            $this->addBlock($p->pid, $this->time, $this->time + $p->burst);
            $this->time += $p->burst;
            $p->completion = $this->time;
            $left = array_filter($left, fn($x) => $x !== $p);   // remove finished process
        }
    }

    // ---------- Round Robin (preemptive) ----------
    private function rr(int $quantum): void {
        $pending = $this->byArrival($this->procs); // not yet queued, sorted by arrival
        $queue = [];                                // FIFO ready queue
        $idx = 0; $done = 0; $n = count($pending);
        // Move every process with arrival <= currentTime from "pending" into the queue
        $enqueueArrivals = function () use (&$pending, &$queue, &$idx, $n) {
            while ($idx < $n && $pending[$idx]->arrival <= $this->time) $queue[] = $pending[$idx++];
        };
        while ($done < $n) {
            $enqueueArrivals();
            if (!$queue) {                          // queue empty -> CPU idle until next arrival
                $next = $pending[$idx]->arrival;
                $this->addBlock('IDLE', $this->time, $next);
                $this->time = $next;
                continue;
            }
            $p = array_shift($queue);               // take head of the queue
            $run = min($quantum, $p->remaining);    // run one slice (or less if it finishes)
            $this->addBlock($p->pid, $this->time, $this->time + $run);
            $this->time += $run;
            $p->remaining -= $run;
            $enqueueArrivals();                     // CRITICAL RULE: new arrivals enter BEFORE the preempted process
            if ($p->remaining > 0) $queue[] = $p;   // preempted -> back to the tail
            else { $p->completion = $this->time; $done++; }
        }
    }

    // ---------- Run chosen algorithm and build the JSON-ready result ----------
    public function run(string $algo, int $quantum = 1): array {
        if ($algo === 'FCFS') $this->fcfs();
        elseif ($algo === 'SJF') $this->sjf();
        else $this->rr($quantum);

        usort($this->procs, fn($a, $b) => $a->order <=> $b->order); // restore original input order
        $sumT = $sumW = 0;
        foreach ($this->procs as $p) { $p->computeMetrics(); $sumT += $p->turnaround; $sumW += $p->waiting; }
        $n = count($this->procs);
        return [
            'gantt'     => $this->gantt,
            'processes' => array_map(fn($p) => $p->toArray(), $this->procs),
            'avgTat'    => round($sumT / $n, 2),
            'avgWt'     => round($sumW / $n, 2),
        ];
    }
}
