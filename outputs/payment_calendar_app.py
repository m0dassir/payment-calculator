import calendar
import json
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


DATA_FILE = Path.home() / "Documents" / "PaymentCalendarData.json"

THEMES = {
    "Light": {
        "bg": "#f5f7fb",
        "text": "#17202a",
        "muted": "#4d5b6a",
        "field": "#ffffff",
        "button": "#e8edf5",
        "button_active": "#dce5f2",
        "today": "#dce8ff",
        "filled": "#e8f7ed",
        "select": "#bfd7ff",
    },
    "Dark": {
        "bg": "#1f2329",
        "text": "#f2f5f8",
        "muted": "#c5ccd6",
        "field": "#181c22",
        "button": "#3a414b",
        "button_active": "#46505d",
        "today": "#344966",
        "filled": "#234634",
        "select": "#48658f",
    },
}


def format_currency(amount):
    return f"{amount:,.0f} BDT"


def month_key(year, month):
    return f"{year:04d}-{month:02d}"


def generate_report(total_classes, class_earnings, daily_log, exam_count, paper_rate, month_name, year):
    paper_earnings = exam_count * paper_rate
    final_total = class_earnings + paper_earnings

    lines = []
    lines.append("========= MONTHLY CLASS SUMMARY =========\n")
    lines.append(f"Month: {month_name} {year}\n")

    lines.append("--- Daily Breakdown ---")
    for day, classes, earnings in daily_log:
        if classes:
            lines.append(f"{month_name} {day:02d} -> {classes} classes -> {format_currency(earnings)}")

    lines.append("\n--- Totals ---")
    lines.append(f"Total Classes: {total_classes}")
    lines.append(f"Class Earnings: {format_currency(class_earnings)}")

    lines.append(f"\nExam Papers Checked: {exam_count}")
    lines.append(f"Paper Rate: {format_currency(paper_rate)}")
    lines.append(f"Paper Earnings: {format_currency(paper_earnings)}")

    lines.append("\n----------------------------------")
    lines.append(f"FINAL PAYMENT: {format_currency(final_total)}")
    lines.append("==================================")

    return "\n".join(lines)


class PaymentCalendarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Payment Calendar")
        self.root.geometry("980x680")
        self.root.minsize(860, 600)

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        now = datetime.now()
        self.year = now.year
        self.month = now.month
        self.selected_day = now.day
        self.day_buttons = {}
        self.data = self.load_data()
        self.last_report = ""

        settings = self.data.setdefault("settings", {})
        self.class_rate_var = tk.StringVar(value=str(settings.get("class_rate", "")))
        self.paper_rate_var = tk.StringVar(value=str(settings.get("paper_rate", "5")))
        self.exam_count_var = tk.StringVar(value="0")
        self.selected_classes_var = tk.StringVar(value="0")
        self.theme_var = tk.StringVar(value=settings.get("theme", "Light"))
        self.month_title_var = tk.StringVar()
        self.selected_day_var = tk.StringVar()
        self.summary_var = tk.StringVar()
        self.status_var = tk.StringVar(value=f"Data is saved automatically to {DATA_FILE}")

        self.build_ui()
        self.load_month_settings()
        self.refresh_calendar()
        self.apply_theme()

    def load_data(self):
        if not DATA_FILE.exists():
            return {"settings": {}, "months": {}}
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"settings": {}, "months": {}}

    def save_data(self):
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def current_month_data(self):
        months = self.data.setdefault("months", {})
        key = month_key(self.year, self.month)
        return months.setdefault(
            key,
            {
                "class_rate": self.class_rate_var.get(),
                "paper_rate": self.paper_rate_var.get(),
                "exam_count": self.exam_count_var.get(),
                "classes": {},
            },
        )

    def build_ui(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        top = ttk.Frame(outer)
        top.pack(fill=tk.X)

        ttk.Button(top, text="<", width=4, command=self.previous_month).pack(side=tk.LEFT)
        ttk.Label(top, textvariable=self.month_title_var, font=("Segoe UI", 15, "bold")).pack(side=tk.LEFT, padx=12)
        ttk.Button(top, text=">", width=4, command=self.next_month).pack(side=tk.LEFT)

        ttk.Label(top, text="Theme").pack(side=tk.RIGHT, padx=(12, 6))
        theme_box = ttk.Combobox(top, textvariable=self.theme_var, values=list(THEMES.keys()), width=10, state="readonly")
        theme_box.pack(side=tk.RIGHT)
        theme_box.bind("<<ComboboxSelected>>", lambda _event: self.on_setting_change())

        main = ttk.PanedWindow(outer, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, pady=(12, 8))

        calendar_panel = ttk.Frame(main)
        side_panel = ttk.Frame(main)
        main.add(calendar_panel, weight=3)
        main.add(side_panel, weight=2)

        weekdays = ttk.Frame(calendar_panel)
        weekdays.pack(fill=tk.X)
        for name in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            ttk.Label(weekdays, text=name, anchor=tk.CENTER).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.calendar_grid = ttk.Frame(calendar_panel)
        self.calendar_grid.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        ttk.Label(side_panel, textvariable=self.selected_day_var, font=("Segoe UI", 12, "bold")).pack(anchor=tk.W)

        form = ttk.Frame(side_panel)
        form.pack(fill=tk.X, pady=(8, 10))

        ttk.Label(form, text="Classes for selected day").grid(row=0, column=0, sticky=tk.W, pady=(0, 4))
        classes_entry = ttk.Entry(form, textvariable=self.selected_classes_var, width=14)
        classes_entry.grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        classes_entry.bind("<FocusOut>", lambda _event: self.save_selected_day())
        classes_entry.bind("<Return>", lambda _event: self.save_selected_day())

        ttk.Label(form, text="Class rate (BDT)").grid(row=2, column=0, sticky=tk.W, pady=(0, 4))
        class_rate_entry = ttk.Entry(form, textvariable=self.class_rate_var, width=14)
        class_rate_entry.grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        class_rate_entry.bind("<FocusOut>", lambda _event: self.on_setting_change())
        class_rate_entry.bind("<Return>", lambda _event: self.on_setting_change())

        ttk.Label(form, text="Paper rate (BDT)").grid(row=4, column=0, sticky=tk.W, pady=(0, 4))
        paper_rate_entry = ttk.Entry(form, textvariable=self.paper_rate_var, width=14)
        paper_rate_entry.grid(row=5, column=0, sticky=tk.W, pady=(0, 10))
        paper_rate_entry.bind("<FocusOut>", lambda _event: self.on_setting_change())
        paper_rate_entry.bind("<Return>", lambda _event: self.on_setting_change())

        ttk.Label(form, text="Exam papers checked").grid(row=6, column=0, sticky=tk.W, pady=(0, 4))
        exam_entry = ttk.Entry(form, textvariable=self.exam_count_var, width=14)
        exam_entry.grid(row=7, column=0, sticky=tk.W, pady=(0, 10))
        exam_entry.bind("<FocusOut>", lambda _event: self.on_setting_change())
        exam_entry.bind("<Return>", lambda _event: self.on_setting_change())

        ttk.Button(form, text="Save Day", command=self.save_selected_day).grid(row=8, column=0, sticky=tk.W)

        ttk.Label(side_panel, textvariable=self.summary_var, justify=tk.LEFT).pack(anchor=tk.W, pady=(6, 10))

        self.report_text = tk.Text(side_panel, wrap=tk.WORD, height=12)
        self.report_text.pack(fill=tk.BOTH, expand=True)

        actions = ttk.Frame(outer)
        actions.pack(fill=tk.X)
        ttk.Button(actions, text="Generate Monthly Report", command=self.generate).pack(side=tk.LEFT)
        ttk.Button(actions, text="Save Report", command=self.save_report).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Label(actions, textvariable=self.status_var).pack(side=tk.LEFT, padx=(16, 0))

    def apply_theme(self):
        colors = THEMES[self.theme_var.get()]
        self.root.configure(bg=colors["bg"])
        self.style.configure(".", background=colors["bg"], foreground=colors["text"])
        self.style.configure("TFrame", background=colors["bg"])
        self.style.configure("TLabel", background=colors["bg"], foreground=colors["text"])
        self.style.configure("TButton", background=colors["button"], foreground=colors["text"])
        self.style.map("TButton", background=[("active", colors["button_active"])])
        self.style.configure("TEntry", fieldbackground=colors["field"], foreground=colors["text"])
        self.style.configure("TCombobox", fieldbackground=colors["field"], foreground=colors["text"])
        self.style.configure("TPanedwindow", background=colors["bg"])
        self.style.configure("Day.TButton", background=colors["button"], foreground=colors["text"])
        self.style.configure("FilledDay.TButton", background=colors["filled"], foreground=colors["text"])
        self.style.configure("Today.TButton", background=colors["today"], foreground=colors["text"])
        self.style.configure("SelectedDay.TButton", background=colors["select"], foreground=colors["text"])
        self.report_text.configure(
            bg=colors["field"],
            fg=colors["text"],
            insertbackground=colors["text"],
            selectbackground=colors["select"],
            relief=tk.FLAT,
        )
        self.refresh_day_styles()

    def validate_int(self, value, label):
        try:
            number = int(value or "0")
        except ValueError:
            raise ValueError(f"{label} must be a whole number.")
        if number < 0:
            raise ValueError(f"{label} cannot be negative.")
        return number

    def validate_rate(self, value, label, allow_zero=False):
        try:
            number = float(value)
        except ValueError:
            raise ValueError(f"{label} must be a number.")
        if allow_zero:
            if number < 0:
                raise ValueError(f"{label} cannot be negative.")
        elif number <= 0:
            raise ValueError(f"{label} must be positive.")
        return number

    def load_month_settings(self):
        month_data = self.current_month_data()
        self.class_rate_var.set(str(month_data.get("class_rate", self.data["settings"].get("class_rate", ""))))
        self.paper_rate_var.set(str(month_data.get("paper_rate", self.data["settings"].get("paper_rate", "5"))))
        self.exam_count_var.set(str(month_data.get("exam_count", "0")))

    def previous_month(self):
        self.save_selected_day(show_status=False)
        if self.month == 1:
            self.month = 12
            self.year -= 1
        else:
            self.month -= 1
        self.selected_day = 1
        self.load_month_settings()
        self.refresh_calendar()

    def next_month(self):
        self.save_selected_day(show_status=False)
        if self.month == 12:
            self.month = 1
            self.year += 1
        else:
            self.month += 1
        self.selected_day = 1
        self.load_month_settings()
        self.refresh_calendar()

    def select_day(self, day):
        self.save_selected_day(show_status=False)
        self.selected_day = day
        self.load_selected_day()
        self.refresh_day_styles()

    def load_selected_day(self):
        month_data = self.current_month_data()
        classes = month_data.get("classes", {}).get(str(self.selected_day), "0")
        self.selected_classes_var.set(str(classes))
        self.selected_day_var.set(f"{calendar.month_name[self.month]} {self.selected_day}, {self.year}")

    def save_selected_day(self, show_status=True):
        try:
            classes = self.validate_int(self.selected_classes_var.get(), "Classes")
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            self.load_selected_day()
            return False

        month_data = self.current_month_data()
        month_data.setdefault("classes", {})[str(self.selected_day)] = classes
        self.save_month_settings(show_status=False)
        self.save_data()
        self.update_summary()
        self.refresh_day_styles()
        if show_status:
            self.status_var.set("Saved.")
        return True

    def save_month_settings(self, show_status=True):
        try:
            self.validate_rate(self.class_rate_var.get(), "Class rate")
            self.validate_rate(self.paper_rate_var.get(), "Paper rate", allow_zero=True)
            self.validate_int(self.exam_count_var.get(), "Exam papers checked")
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return False

        month_data = self.current_month_data()
        month_data["class_rate"] = self.class_rate_var.get()
        month_data["paper_rate"] = self.paper_rate_var.get()
        month_data["exam_count"] = self.exam_count_var.get()
        settings = self.data.setdefault("settings", {})
        settings["class_rate"] = self.class_rate_var.get()
        settings["paper_rate"] = self.paper_rate_var.get()
        settings["theme"] = self.theme_var.get()
        self.save_data()
        self.update_summary()
        self.apply_theme()
        if show_status:
            self.status_var.set("Settings saved.")
        return True

    def on_setting_change(self):
        self.save_month_settings()

    def refresh_calendar(self):
        for child in self.calendar_grid.winfo_children():
            child.destroy()
        self.day_buttons = {}

        month_name = calendar.month_name[self.month]
        self.month_title_var.set(f"{month_name} {self.year}")
        month_weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(self.year, self.month)

        for row_index, week in enumerate(month_weeks):
            self.calendar_grid.rowconfigure(row_index, weight=1)
            for col_index, day in enumerate(week):
                self.calendar_grid.columnconfigure(col_index, weight=1)
                if day == 0:
                    ttk.Label(self.calendar_grid, text="").grid(row=row_index, column=col_index, sticky="nsew", padx=3, pady=3)
                    continue
                button = ttk.Button(self.calendar_grid, command=lambda selected=day: self.select_day(selected))
                button.grid(row=row_index, column=col_index, sticky="nsew", padx=3, pady=3)
                self.day_buttons[day] = button

        days_in_month = calendar.monthrange(self.year, self.month)[1]
        if self.selected_day > days_in_month:
            self.selected_day = days_in_month
        self.load_selected_day()
        self.update_summary()
        self.refresh_day_styles()

    def refresh_day_styles(self):
        if not self.day_buttons:
            return
        month_data = self.current_month_data()
        classes_by_day = month_data.get("classes", {})
        today = datetime.now()

        for day, button in self.day_buttons.items():
            classes = self.validate_int(str(classes_by_day.get(str(day), "0")), "Classes")
            label = f"{day}\n{classes} classes" if classes else str(day)
            style = "Day.TButton"
            if classes:
                style = "FilledDay.TButton"
            if today.year == self.year and today.month == self.month and today.day == day:
                style = "Today.TButton"
            if day == self.selected_day:
                style = "SelectedDay.TButton"
            button.configure(text=label, style=style)

    def calculate_month(self):
        class_rate = self.validate_rate(self.class_rate_var.get(), "Class rate")
        paper_rate = self.validate_rate(self.paper_rate_var.get(), "Paper rate", allow_zero=True)
        exam_count = self.validate_int(self.exam_count_var.get(), "Exam papers checked")

        month_data = self.current_month_data()
        days = calendar.monthrange(self.year, self.month)[1]
        daily_log = []
        total_classes = 0
        class_earnings = 0

        for day in range(1, days + 1):
            classes = self.validate_int(str(month_data.get("classes", {}).get(str(day), "0")), "Classes")
            earnings = classes * class_rate
            total_classes += classes
            class_earnings += earnings
            daily_log.append((day, classes, earnings))

        return total_classes, class_earnings, daily_log, exam_count, paper_rate

    def update_summary(self):
        try:
            total_classes, class_earnings, _daily_log, exam_count, paper_rate = self.calculate_month()
        except ValueError:
            return

        paper_earnings = exam_count * paper_rate
        final_total = class_earnings + paper_earnings
        self.summary_var.set(
            "\n".join(
                [
                    f"Classes this month: {total_classes}",
                    f"Class earnings: {format_currency(class_earnings)}",
                    f"Paper earnings: {format_currency(paper_earnings)}",
                    f"Final payment: {format_currency(final_total)}",
                ]
            )
        )

    def generate(self):
        if not self.save_selected_day(show_status=False):
            return
        if not self.save_month_settings(show_status=False):
            return

        try:
            total_classes, class_earnings, daily_log, exam_count, paper_rate = self.calculate_month()
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        self.last_report = generate_report(
            total_classes,
            class_earnings,
            daily_log,
            exam_count,
            paper_rate,
            calendar.month_name[self.month],
            self.year,
        )
        self.report_text.delete("1.0", tk.END)
        self.report_text.insert(tk.END, self.last_report)
        self.status_var.set("Monthly report generated.")

    def save_report(self):
        if not self.last_report:
            self.generate()
            if not self.last_report:
                return

        default_name = f"payment_{calendar.month_name[self.month]}_{self.year}.txt"
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


def main():
    root = tk.Tk()
    PaymentCalendarApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
