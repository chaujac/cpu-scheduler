"""scheduler.py - pure scheduling engines + metrics. No tkinter, no input() - easy to test."""

from collections import deque
from dataclasses import dataclass
from models import Process, GanttSegment, validate_quantum


@dataclass
class ScheduleResult:
    processes: list  # finished Process objects, ordered by input_index
    segments: list  # GanttSegment list (includes IDLE)
    avg_tat: float
    avg_wt: float
    total_span: int  # end time of the last segment (timeline starts at 0)
    idle_total: int


def _clone(processes):
    """Work on fresh copies so the caller's data is never changed."""
    return [Process(p.pid, p.arrival_time, p.burst_time, p.input_index) for p in processes]


def _idle(segments, start, end):
    segments.append(GanttSegment("IDLE", start, end, True))


def _finish(procs, segments) -> ScheduleResult:
    """Apply TAT = CT - AT and WT = TAT - BT, average, and restore input order."""
    for p in procs:
        p.turnaround_time = p.completion_time - p.arrival_time
        p.waiting_time = p.turnaround_time - p.burst_time
    procs = sorted(procs, key=lambda p: p.input_index)  # restore original order
    n = len(procs)
    idle = sum(s.end - s.start for s in segments if s.is_idle)
    return ScheduleResult(
        procs,
        segments,
        round(sum(p.turnaround_time for p in procs) / n, 2),
        round(sum(p.waiting_time for p in procs) / n, 2),
        segments[-1].end,
        idle,
    )


def run_fcfs(processes) -> ScheduleResult:
    """Non-preemptive: earliest arrival first, ties -> input_index."""
    procs, segs, t = _clone(processes), [], 0
    for p in sorted(procs, key=lambda p: (p.arrival_time, p.input_index)):
        if t < p.arrival_time:  # CPU idle: jump clock to the arrival
            _idle(segs, t, p.arrival_time)
            t = p.arrival_time
        segs.append(GanttSegment(p.pid, t, t + p.burst_time))
        t += p.burst_time
        p.remaining_time = 0
        p.completion_time = t
    return _finish(procs, segs)


def run_sjf(processes) -> ScheduleResult:
    """Non-preemptive: among arrived, unfinished processes pick smallest burst."""
    procs, segs, t = _clone(processes), [], 0
    waiting = list(procs)  # not yet completed
    while waiting:
        ready = [p for p in waiting if p.arrival_time <= t]
        if not ready:  # nobody has arrived -> idle until earliest arrival
            nxt = min(p.arrival_time for p in waiting)
            _idle(segs, t, nxt)
            t = nxt
            continue
        # tie-break chain: burst, then arrival, then input order
        p = min(ready, key=lambda p: (p.burst_time, p.arrival_time, p.input_index))
        segs.append(GanttSegment(p.pid, t, t + p.burst_time))
        t += p.burst_time
        p.remaining_time = 0
        p.completion_time = t
        waiting.remove(p)
    return _finish(procs, segs)


def run_round_robin(processes, time_quantum) -> ScheduleResult:
    """Preemptive: FIFO ready queue (deque), fixed time slices."""
    tq = validate_quantum(time_quantum)
    procs, segs, t = _clone(processes), [], 0
    not_arrived = sorted(procs, key=lambda p: (p.arrival_time, p.input_index))
    queue, done = deque(), 0

    def admit():
        """Move every process with arrival <= current time into the queue (in arrival order)."""
        while not_arrived and not_arrived[0].arrival_time <= t:
            queue.append(not_arrived.pop(0))

    while done < len(procs):
        admit()
        if not queue:  # queue empty -> idle until next arrival
            nxt = not_arrived[0].arrival_time
            _idle(segs, t, nxt)
            t = nxt
            continue
        p = queue.popleft()  # head of the queue gets the CPU
        slice_len = min(tq, p.remaining_time)
        segs.append(GanttSegment(p.pid, t, t + slice_len))
        t += slice_len
        p.remaining_time -= slice_len  # burst_time stays untouched
        admit()  # NEW arrivals first ...
        if p.remaining_time > 0:
            queue.append(p)  # ... THEN the preempted process goes to the tail
        else:
            p.completion_time = t
            done += 1
    return _finish(procs, segs)


def verify_timeline(result: ScheduleResult) -> bool:
    """Conservation check: Total Span = sum(BT) + sum(IDLE), and segments are gapless from t=0."""
    expected, ok = 0, True
    for s in result.segments:
        ok &= s.start == expected  # each segment starts where the last one ended
        expected = s.end
    total_bt = sum(p.burst_time for p in result.processes)
    return bool(ok and result.total_span == total_bt + result.idle_total)
