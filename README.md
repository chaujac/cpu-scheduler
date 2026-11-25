# CPU Scheduling Simulator

**CS 3104N Operating Systems: Final Term Project**
University of San Carlos, **Group 9** (John Andrew Chua and Bab Amber Moday)

A standalone desktop simulator for three CPU scheduling algorithms, written in pure Python.
It uses only the standard library (`tkinter` for the GUI), so there is nothing to install.

## Features

- **Algorithms:** First-Come First-Served (non-preemptive), Shortest-Job-First (non-preemptive), Round Robin (preemptive)
- Editable process table with add and remove rows
- Load processes from **CSV** or **JSON** files, or use the built-in presets
- Time Quantum input that is enabled only for Round Robin
- Color-coded **Gantt chart** with timestamps and explicit **IDLE** blocks
- Results table (PID, AT, BT, CT, TAT, WT) in original input order
- Average Turnaround Time and Average Waiting Time cards (2 decimal places)
- Timeline conservation check: `Total Span = sum(BT) + sum(IDLE)`
- Clear error dialogs for invalid input (no crashes or hangs)

## Requirements

- Python 3.8 or newer
- `tkinter` (bundled with the standard Python installers for Windows and macOS; on Debian/Ubuntu run `sudo apt install python3-tk`)

## Usage

```bash
python main.py          # launch the GUI
python main.py --cli    # run the terminal self-test (no display needed)
```

## Project structure

| File | Responsibility |
|---|---|
| `main.py` | Entry point; GUI by default, `--cli` runs verification tests |
| `models.py` | `Process`, `GanttSegment`, `ValidationError`, input validation helpers |
| `scheduler.py` | `run_fcfs`, `run_sjf`, `run_round_robin`, metrics, `verify_timeline` |
| `presets.py` | Built-in datasets (including the edge case) and CSV/JSON loading |
| `gui.py` | tkinter interface and canvas Gantt chart |
| `DEFENSE_CHEATSHEET.md` | Algorithm summary and hand-traced edge-case example |

Scheduling logic lives in `scheduler.py` and never imports `tkinter`, so it can be tested and explained separately from the UI.

## Scheduling rules

| Algorithm | Selection rule | Tie-break |
|---|---|---|
| FCFS | Earliest arrival first | `input_index` |
| SJF | Smallest burst among arrived, unfinished processes | arrival, then `input_index` |
| RR | FIFO queue; each turn runs `min(TQ, remaining)` | arrival, then `input_index` |

- **Idle CPU:** if no process has arrived, the clock jumps to the next arrival and an `IDLE` segment is recorded.
- **Round Robin queue rule:** after a time slice, newly arrived processes are enqueued *before* the preempted process rejoins the tail.
- **Metrics:** `TAT = CT - AT` and `WT = TAT - BT`. `burst_time` is never modified; `remaining_time` counts down instead.

## Input file formats

**CSV** (header row optional):

```csv
pid,arrival,burst
P1,0,5
P2,1,3
```

**JSON:**

```json
[
  {"pid": "P1", "arrival": 0, "burst": 5},
  {"pid": "P2", "arrival": 1, "burst": 3}
]
```

## Input validation

The simulator rejects:

- an empty process list
- blank or duplicate PIDs
- non-integer or negative arrival times
- non-integer or zero/negative burst times
- non-integer or zero/negative time quantum

## Edge-case preset

| PID | AT | BT |
|---|---|---|
| P1 | 5 | 2 |
| P2 | 2 | 3 |
| P3 | 12 | 4 |
| P4 | 2 | 1 |

Expected results (Round Robin with TQ = 2):

| Algorithm | Avg TAT | Avg WT |
|---|---|---|
| FCFS | 3.50 | 1.00 |
| SJF | 3.00 | 0.50 |
| RR | 3.50 | 1.00 |

See `DEFENSE_CHEATSHEET.md` for the full step-by-step traces.