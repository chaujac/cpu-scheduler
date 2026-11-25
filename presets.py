"""presets.py - built-in datasets + CSV/JSON loading. Rows are (pid, arrival, burst)."""

import csv
import json
from models import ValidationError

PRESETS = {
    # Edge case: idle at t=0, arrival tie at t=2 (P2 vs P4), idle gap 8-12
    "Edge Case": [("P1", 5, 2), ("P2", 2, 3), ("P3", 12, 4), ("P4", 2, 1)],
    "Sample A": [("P1", 0, 5), ("P2", 1, 3), ("P3", 2, 8), ("P4", 3, 6)],
    "Sample B": [("P1", 0, 7), ("P2", 2, 4), ("P3", 4, 1), ("P4", 5, 4)],
}


def load_file(path):
    """Load rows from .csv (header optional: pid,arrival,burst) or .json (list of objects)."""
    try:
        if path.lower().endswith(".json"):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return [
                (
                    d["pid"],
                    d.get("arrival", d.get("arrival_time")),
                    d.get("burst", d.get("burst_time")),
                )
                for d in data
            ]
        with open(path, newline="", encoding="utf-8") as f:
            rows = [r for r in csv.reader(f) if r]
        if rows and rows[0][0].strip().lower() == "pid":  # skip header line
            rows = rows[1:]
        return [(r[0], r[1], r[2]) for r in rows]
    except (OSError, ValueError, KeyError, IndexError, TypeError) as e:
        raise ValidationError(f"Could not read file: {e}")
