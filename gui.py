"""gui.py - tkinter front end. Only draws + collects input; all logic lives in scheduler.py."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from models import ValidationError, validate_processes, validate_quantum
from scheduler import run_fcfs, run_sjf, run_round_robin, verify_timeline
from presets import PRESETS, load_file

PALETTE = ["#a78bfa", "#22d3ee", "#fbbf24", "#34d399", "#f472b6", "#60a5fa", "#fb923c", "#a3e635"]
BG, PANEL, FG = "#1b1230", "#261a45", "#ece6fa"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CPU Scheduler - CS 3104N - Group 9")
        self.configure(bg=BG)
        self.geometry("1100x720")
        self.entry_rows = []  # [(frame, pid_var, at_var, bt_var)]
        self.algo = tk.StringVar(value="FCFS")
        self.tq = tk.StringVar(value="2")
        self._build()
        self.set_rows(PRESETS["Sample A"])
        self._update_tq_state()

    # ---------- layout ----------
    def _build(self):
        left = tk.Frame(self, bg=PANEL, padx=12, pady=12)
        left.pack(side="left", fill="y")
        tk.Label(left, text="CPU Scheduler", bg=PANEL, fg=FG, font=("Segoe UI", 16, "bold")).pack(
            anchor="w"
        )
        tk.Label(left, text="CS 3104N - Group 9", bg=PANEL, fg="#a699c9").pack(
            anchor="w", pady=(0, 10)
        )

        head = tk.Frame(left, bg=PANEL)
        head.pack(fill="x")
        for text in ("PID", "Arrival", "Burst"):
            tk.Label(head, text=text, bg=PANEL, fg="#a699c9", width=9, anchor="w").pack(side="left")
        self.rows_frame = tk.Frame(left, bg=PANEL)
        self.rows_frame.pack(fill="x")

        bar = tk.Frame(left, bg=PANEL)
        bar.pack(fill="x", pady=8)
        ttk.Button(bar, text="+ Add Process", command=self.add_row).pack(side="left")
        ttk.Button(bar, text="Load CSV/JSON", command=self.open_file).pack(side="left", padx=6)

        tk.Label(left, text="Presets", bg=PANEL, fg=FG).pack(anchor="w", pady=(8, 2))
        for name, rows in PRESETS.items():
            ttk.Button(left, text=name, command=lambda r=rows: self.set_rows(r)).pack(
                fill="x", pady=1
            )

        tk.Label(left, text="Algorithm", bg=PANEL, fg=FG).pack(anchor="w", pady=(12, 2))
        for label, val in (("FCFS", "FCFS"), ("SJF", "SJF"), ("Round Robin", "RR")):
            tk.Radiobutton(
                left,
                text=label,
                variable=self.algo,
                value=val,
                command=self._update_tq_state,
                bg=PANEL,
                fg=FG,
                selectcolor=BG,
                activebackground=PANEL,
                activeforeground=FG,
            ).pack(anchor="w")
        tqf = tk.Frame(left, bg=PANEL)
        tqf.pack(anchor="w", pady=6)
        tk.Label(tqf, text="Time quantum", bg=PANEL, fg=FG).pack(side="left")
        self.tq_entry = ttk.Entry(tqf, textvariable=self.tq, width=6)
        self.tq_entry.pack(side="left", padx=6)
        ttk.Button(left, text="Run Simulation", command=self.run).pack(fill="x", pady=10, ipady=6)

        right = tk.Frame(self, bg=BG, padx=12, pady=12)
        right.pack(side="left", fill="both", expand=True)
        tk.Label(right, text="Gantt chart", bg=BG, fg=FG, font=("Segoe UI", 12, "bold")).pack(
            anchor="w"
        )
        self.canvas = tk.Canvas(right, height=120, bg="#150e28", highlightthickness=0)
        sx = ttk.Scrollbar(right, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=sx.set)
        self.canvas.pack(fill="x")
        sx.pack(fill="x")

        cards = tk.Frame(right, bg=BG)
        cards.pack(fill="x", pady=10)
        self.lbl_tat = self._card(cards, "Average Turnaround Time")
        self.lbl_wt = self._card(cards, "Average Waiting Time")
        self.lbl_chk = tk.Label(cards, text="", bg=BG, fg="#a699c9")
        self.lbl_chk.pack(side="left", padx=10)

        cols = ("PID", "AT", "BT", "CT", "TAT", "WT")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", height=10)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=80, anchor="center")
        self.tree.pack(fill="both", expand=True)

    def _card(self, parent, title):
        f = tk.Frame(parent, bg=PANEL, padx=14, pady=8)
        f.pack(side="left", padx=(0, 10))
        tk.Label(f, text=title, bg=PANEL, fg="#a699c9").pack(anchor="w")
        lbl = tk.Label(f, text="-", bg=PANEL, fg=FG, font=("Segoe UI", 18, "bold"))
        lbl.pack(anchor="w")
        return lbl

    # ---------- input table ----------
    def add_row(self, pid=None, at="0", bt="1"):
        pid = pid if pid is not None else f"P{len(self.entry_rows) + 1}"
        f = tk.Frame(self.rows_frame, bg=PANEL)
        f.pack(fill="x", pady=1)
        vars_ = [tk.StringVar(value=str(v)) for v in (pid, at, bt)]
        for v in vars_:
            ttk.Entry(f, textvariable=v, width=9).pack(side="left", padx=1)
        row = (f, *vars_)
        ttk.Button(f, text="x", width=3, command=lambda r=row: self.remove_row(r)).pack(
            side="left", padx=2
        )
        self.entry_rows.append(row)

    def remove_row(self, row):
        row[0].destroy()
        self.entry_rows.remove(row)

    def set_rows(self, rows):
        for r in list(self.entry_rows):
            self.remove_row(r)
        for pid, at, bt in rows:
            self.add_row(pid, at, bt)

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("CSV/JSON", "*.csv *.json")])
        if path:
            try:
                self.set_rows(load_file(path))
            except ValidationError as e:
                messagebox.showerror("Load error", str(e))

    def _update_tq_state(self):  # quantum box only usable for Round Robin
        self.tq_entry.config(state="normal" if self.algo.get() == "RR" else "disabled")

    # ---------- run + display ----------
    def run(self):
        try:
            procs = validate_processes(
                [(p.get(), a.get(), b.get()) for _, p, a, b in self.entry_rows]
            )
            algo = self.algo.get()
            if algo == "FCFS":
                res = run_fcfs(procs)
            elif algo == "SJF":
                res = run_sjf(procs)
            else:
                res = run_round_robin(procs, validate_quantum(self.tq.get()))
        except ValidationError as e:
            messagebox.showerror("Invalid input", str(e))
            return
        self.draw_gantt(res)
        self.tree.delete(*self.tree.get_children())
        for p in res.processes:  # already in input order
            self.tree.insert(
                "",
                "end",
                values=(
                    p.pid,
                    p.arrival_time,
                    p.burst_time,
                    p.completion_time,
                    p.turnaround_time,
                    p.waiting_time,
                ),
            )
        self.lbl_tat.config(text=f"{res.avg_tat:.2f}")
        self.lbl_wt.config(text=f"{res.avg_wt:.2f}")
        self.lbl_chk.config(
            text="Timeline check: "
            + ("OK" if verify_timeline(res) else "FAILED")
            + f" (span {res.total_span} = BT + idle {res.idle_total})"
        )

    def draw_gantt(self, res):
        c = self.canvas
        c.delete("all")
        unit = max(22, min(60, 900 // max(res.total_span, 1)))  # pixels per time unit
        x0, y0, h = 20, 20, 50
        color = {p.pid: PALETTE[p.input_index % len(PALETTE)] for p in res.processes}
        for s in res.segments:
            xa, xb = x0 + s.start * unit, x0 + s.end * unit
            if s.is_idle:
                c.create_rectangle(
                    xa, y0, xb, y0 + h, fill="#4a3f6b", outline="#a699c9", stipple="gray50"
                )
                c.create_text((xa + xb) / 2, y0 + h / 2, text="IDLE", fill="#ece6fa")
            else:
                c.create_rectangle(xa, y0, xb, y0 + h, fill=color[s.label], outline=BG, width=2)
                c.create_text(
                    (xa + xb) / 2,
                    y0 + h / 2,
                    text=s.label,
                    fill="#0d0820",
                    font=("Segoe UI", 10, "bold"),
                )
            c.create_text(xa, y0 + h + 14, text=str(s.start), fill=FG)  # start timestamp
        c.create_text(
            x0 + res.total_span * unit, y0 + h + 14, text=str(res.total_span), fill=FG
        )  # final end
        c.configure(scrollregion=(0, 0, x0 * 2 + res.total_span * unit, 100))
