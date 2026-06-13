import calendar
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


PAPER_RATE = 5


def format_currency(amount):
    return f"{amount:,.0f} BDT"


def generate_report(total_classes, class_earnings, daily_log, exam_count, month_name, year):
    paper_earnings = exam_count * PAPER_RATE
    final_total = class_earnings + paper_earnings

    lines = []
    lines.append("========= PAYMENT SUMMARY =========\n")
    lines.append(f"Month: {month_name} {year}\n")

    lines.append("--- Daily Breakdown ---")
    for day, classes, earnings in daily_log:
        lines.append(f"{month_name} {day:02d} -> {classes} classes -> {format_currency(earnings)}")

    lines.append("\n--- Totals ---")
    lines.append(f"Total Classes: {total_classes}")
    lines.append(f"Class Earnings: {format_currency(class_earnings)}")

    lines.append(f"\nExam Papers Checked: {exam_count}")
    lines.append(f"Paper Earnings: {format_currency(paper_earnings)}")

    lines.append("\n----------------------------------")
    lines.append(f"FINAL PAYMENT: {format_currency(final_total)}")
    lines.append("==================================")

    return "\n".join(lines)


class PaymentCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Payment Calculator")
        self.root.geometry("760x640")
        self.root.minsize(680, 520)

        self.daily_entries = []
        self.last_report = ""

        self.rate_var = tk.StringVar()
        self.exam_var = tk.StringVar(value="0")
        self.month_var = tk.IntVar(value=datetime.now().month)
        self.year_var = tk.IntVar(value=datetime.now().year)
        self.status_var = tk.StringVar(value="Enter details, then click Generate Report.")

        self._build_ui()
        self._rebuild_days()

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        controls = ttk.Frame(outer)
        controls.pack(fill=tk.X)

        ttk.Label(controls, text="Class rate (BDT)").grid(row=0, column=0, sticky=tk.W, padx=(0, 8))
        ttk.Entry(controls, textvariable=self.rate_var, width=16).grid(row=1, column=0, sticky=tk.W, padx=(0, 16))

        ttk.Label(controls, text="Month").grid(row=0, column=1, sticky=tk.W, padx=(0, 8))
        month_box = ttk.Combobox(
            controls,
            textvariable=self.month_var,
            values=list(range(1, 13)),
            width=8,
            state="readonly",
        )
        month_box.grid(row=1, column=1, sticky=tk.W, padx=(0, 16))
        month_box.bind("<<ComboboxSelected>>", lambda _event: self._rebuild_days())

        ttk.Label(controls, text="Year").grid(row=0, column=2, sticky=tk.W, padx=(0, 8))
        year_spin = ttk.Spinbox(
            controls,
            from_=2000,
            to=2100,
            textvariable=self.year_var,
            width=8,
            command=self._rebuild_days,
        )
        year_spin.grid(row=1, column=2, sticky=tk.W, padx=(0, 16))
        year_spin.bind("<FocusOut>", lambda _event: self._rebuild_days())
        year_spin.bind("<Return>", lambda _event: self._rebuild_days())

        ttk.Label(controls, text="Exam papers checked").grid(row=0, column=3, sticky=tk.W, padx=(0, 8))
        ttk.Entry(controls, textvariable=self.exam_var, width=18).grid(row=1, column=3, sticky=tk.W)

        main = ttk.PanedWindow(outer, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, pady=(12, 8))

        days_panel = ttk.Frame(main)
        report_panel = ttk.Frame(main)
        main.add(days_panel, weight=1)
        main.add(report_panel, weight=2)

        ttk.Label(days_panel, text="Daily classes").pack(anchor=tk.W)

        canvas_frame = ttk.Frame(days_panel)
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        self.days_canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        days_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.days_canvas.yview)
        self.days_inner = ttk.Frame(self.days_canvas)

        self.days_inner.bind(
            "<Configure>",
            lambda _event: self.days_canvas.configure(scrollregion=self.days_canvas.bbox("all")),
        )
        self.days_canvas.create_window((0, 0), window=self.days_inner, anchor="nw")
        self.days_canvas.configure(yscrollcommand=days_scroll.set)

        self.days_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        days_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(report_panel, text="Report").pack(anchor=tk.W)
        self.report_text = tk.Text(report_panel, wrap=tk.WORD, height=20)
        self.report_text.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        actions = ttk.Frame(outer)
        actions.pack(fill=tk.X)

        ttk.Button(actions, text="Generate Report", command=self.generate).pack(side=tk.LEFT)
        ttk.Button(actions, text="Save Report", command=self.save_report).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(actions, text="Clear", command=self.clear).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Label(actions, textvariable=self.status_var).pack(side=tk.LEFT, padx=(16, 0))

    def _rebuild_days(self):
        try:
            month = int(self.month_var.get())
            year = int(self.year_var.get())
        except tk.TclError:
            return

        for child in self.days_inner.winfo_children():
            child.destroy()

        self.daily_entries = []
        days = calendar.monthrange(year, month)[1]
        month_name = calendar.month_name[month]

        for day in range(1, days + 1):
            row = ttk.Frame(self.days_inner)
            row.pack(fill=tk.X, pady=2)

            ttk.Label(row, text=f"{month_name} {day:02d}", width=14).pack(side=tk.LEFT)
            value = tk.StringVar(value="0")
            entry = ttk.Entry(row, textvariable=value, width=8)
            entry.pack(side=tk.LEFT)
            self.daily_entries.append((day, value))

    def _read_inputs(self):
        try:
            rate = float(self.rate_var.get())
            if rate <= 0:
                raise ValueError("Class rate must be positive.")
        except ValueError as exc:
            raise ValueError(str(exc) or "Enter a valid class rate.")

        try:
            exam_count = int(self.exam_var.get() or "0")
            if exam_count < 0:
                raise ValueError
        except ValueError:
            raise ValueError("Exam papers checked must be zero or a positive whole number.")

        daily_log = []
        total_classes = 0
        class_earnings = 0

        for day, value in self.daily_entries:
            raw = value.get().strip()
            if raw == "":
                classes = 0
            else:
                try:
                    classes = int(raw)
                except ValueError:
                    raise ValueError(f"Classes for day {day} must be a whole number.")
                if classes < 0:
                    raise ValueError(f"Classes for day {day} cannot be negative.")

            earnings = classes * rate
            total_classes += classes
            class_earnings += earnings
            daily_log.append((day, classes, earnings))

        return rate, total_classes, class_earnings, daily_log, exam_count

    def generate(self):
        try:
            _rate, total_classes, class_earnings, daily_log, exam_count = self._read_inputs()
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        month = int(self.month_var.get())
        year = int(self.year_var.get())
        month_name = calendar.month_name[month]

        self.last_report = generate_report(
            total_classes,
            class_earnings,
            daily_log,
            exam_count,
            month_name,
            year,
        )

        self.report_text.delete("1.0", tk.END)
        self.report_text.insert(tk.END, self.last_report)
        self.status_var.set("Report generated.")

    def save_report(self):
        if not self.last_report:
            self.generate()
            if not self.last_report:
                return

        month = int(self.month_var.get())
        year = int(self.year_var.get())
        month_name = calendar.month_name[month]
        default_name = f"payment_{month_name}_{year}.txt"

        filename = filedialog.asksaveasfilename(
            title="Save report",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not filename:
            return

        Path(filename).write_text(self.last_report, encoding="utf-8")
        self.status_var.set(f"Saved: {filename}")
        messagebox.showinfo("Saved", f"Report saved to:\n{filename}")

    def clear(self):
        self.rate_var.set("")
        self.exam_var.set("0")
        for _day, value in self.daily_entries:
            value.set("0")
        self.report_text.delete("1.0", tk.END)
        self.last_report = ""
        self.status_var.set("Cleared.")


def main():
    root = tk.Tk()
    app = PaymentCalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
