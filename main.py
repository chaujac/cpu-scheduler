"""main.py - entry point.  python main.py  -> GUI   |   python main.py --cli -> terminal self-test."""

import sys
from models import ValidationError, validate_processes
from scheduler import run_fcfs, run_sjf, run_round_robin, verify_timeline
from presets import PRESETS


def cli():
    expected = {
        "FCFS": (3.5, 1.0),
        "SJF": (3.0, 0.5),
        "RR": (3.5, 1.0),
    }  # edge preset, TQ=2 (hand-traced)
    for name, rows in PRESETS.items():
        procs = validate_processes(rows)
        for algo, res in (
            ("FCFS", run_fcfs(procs)),
            ("SJF", run_sjf(procs)),
            ("RR", run_round_robin(procs, 2)),
        ):
            print(f"\n== {name} / {algo} ==")
            print("Gantt:", " ".join(f"[{s.start}-{s.label}-{s.end}]" for s in res.segments))
            for p in res.processes:
                print(
                    f"  {p.pid}: AT={p.arrival_time} BT={p.burst_time} CT={p.completion_time} "
                    f"TAT={p.turnaround_time} WT={p.waiting_time}"
                )
            print(
                f"  Avg TAT={res.avg_tat:.2f}  Avg WT={res.avg_wt:.2f}  timeline_ok={verify_timeline(res)}"
            )
            assert verify_timeline(res)
            if name == "Edge Case":
                assert (res.avg_tat, res.avg_wt) == expected[algo], "edge-case mismatch"
    for bad in (
        [],
        [("", 0, 1)],
        [("P1", -1, 1)],
        [("P1", 0, 0)],
        [("P1", "x", 1)],
        [("P1", 0, 2.5)],
    ):
        try:
            validate_processes(bad)
            raise SystemExit(f"validation missed {bad}")
        except ValidationError as e:
            print("rejected:", e)
    print("\nAll checks passed.")


if __name__ == "__main__":
    if "--cli" in sys.argv:
        cli()
    else:
        from gui import App  # imported lazily so --cli works without a display

        App().mainloop()
