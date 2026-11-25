"""models.py - data classes + input validation (no scheduling logic, no GUI)."""

import re
from dataclasses import dataclass, field


class ValidationError(ValueError):
    """Raised for any bad user input; the GUI shows its message in an error dialog."""


@dataclass
class Process:
    pid: str
    arrival_time: int
    burst_time: int  # IMMUTABLE: never modified, so WT = TAT - BT is always correct
    input_index: int  # original row position: used for tie-breaks + final table order
    remaining_time: int = field(init=False)  # working copy that counts down while running
    completion_time: int = 0
    turnaround_time: int = 0
    waiting_time: int = 0

    def __post_init__(self):
        self.remaining_time = self.burst_time  # starts equal to burst


@dataclass(frozen=True)
class GanttSegment:
    label: str  # PID or "IDLE"
    start: int
    end: int
    is_idle: bool = False


_INT = re.compile(r"[+-]?\d+")  # strict whole-number pattern (rejects "2.5", "abc", "1e3", "")


def parse_int(value, what: str) -> int:
    """Convert raw input to int or raise a clear ValidationError."""
    text = str(value).strip()
    if isinstance(value, bool) or not _INT.fullmatch(text):
        raise ValidationError(f"{what} must be a whole number (got '{text}').")
    return int(text)


def validate_processes(rows) -> list:
    """rows = [(pid, arrival, burst), ...] as raw strings/ints -> list[Process] or ValidationError."""
    if not rows:
        raise ValidationError("Add at least one process.")
    seen, procs = set(), []
    for i, (pid, at, bt) in enumerate(rows):
        n = i + 1
        pid = str(pid).strip()
        if not pid:
            raise ValidationError(f"Row {n}: PID cannot be blank.")
        if pid in seen:
            raise ValidationError(f"Row {n}: PID '{pid}' is duplicated.")
        seen.add(pid)
        at = parse_int(at, f"Row {n}: Arrival time")
        bt = parse_int(bt, f"Row {n}: Burst time")
        if at < 0:
            raise ValidationError(f"Row {n}: Arrival time cannot be negative.")
        if bt <= 0:
            raise ValidationError(f"Row {n}: Burst time must be greater than 0.")
        procs.append(Process(pid, at, bt, i))
    return procs


def validate_quantum(value) -> int:
    tq = parse_int(value, "Time quantum")
    if tq <= 0:
        raise ValidationError("Time quantum must be greater than 0.")
    return tq
