import tkinter as tk
from tkinter import ttk

from pyconsole.process_list import PythonProcess, list_python_processes


class ProcessPanel(ttk.Frame):
    def __init__(self, parent, on_attach=None):
        super().__init__(parent)
        self._on_attach = on_attach
        self._processes: list[PythonProcess] = []
        self._filtered_processes: list[PythonProcess] = []
        self._tooltip_window = None

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=4, pady=4)

        ttk.Label(toolbar, text="Python Processes").pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Refresh", command=self.refresh).pack(side=tk.RIGHT)

        # Search bar
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=4, pady=(0, 4))
        ttk.Label(search_frame, text="Filter:").pack(side=tk.LEFT)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filter())
        search_entry = ttk.Entry(search_frame, textvariable=self._search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

        columns = ("pid", "ppid", "command")
        self._tree = ttk.Treeview(
            self, columns=columns, show="headings", selectmode="browse"
        )
        self._tree.heading("pid", text="PID")
        self._tree.heading("ppid", text="PPID")
        self._tree.heading("command", text="Command")
        self._tree.column("pid", width=60, minwidth=50)
        self._tree.column("ppid", width=60, minwidth=50)
        self._tree.column("command", width=350, minwidth=150)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._tree.bind("<Double-1>", self._on_double_click)
        self._tree.bind("<Motion>", self._on_motion)
        self._tree.bind("<Leave>", self._hide_tooltip)

        ttk.Button(self, text="Attach", command=self._do_attach).pack(
            fill=tk.X, padx=4, pady=4, side=tk.BOTTOM
        )

    def refresh(self):
        self._processes = list_python_processes()
        self._apply_filter()

    def _apply_filter(self):
        self._tree.delete(*self._tree.get_children())
        keyword = self._search_var.get().lower()
        self._filtered_processes = []
        for proc in self._processes:
            if keyword and keyword not in proc.command.lower():
                continue
            self._filtered_processes.append(proc)
            cmd_short = _shorten(proc.command, 60)
            self._tree.insert(
                "", tk.END,
                values=(proc.pid, proc.ppid, cmd_short),
                tags=("ok",) if proc.attachable else ("blocked",),
            )
        self._tree.tag_configure("blocked", foreground="gray")

    def _do_attach(self):
        proc = self._selected_process()
        if proc and self._on_attach:
            self._on_attach(proc)

    def _on_double_click(self, _event):
        self._do_attach()

    def _selected_process(self) -> PythonProcess | None:
        selection = self._tree.selection()
        if not selection:
            return None
        idx = self._tree.index(selection[0])
        if idx < len(self._filtered_processes):
            return self._filtered_processes[idx]
        return None

    # --- Tooltip ---

    def _on_motion(self, event):
        item = self._tree.identify_row(event.y)
        if not item:
            self._hide_tooltip()
            return

        idx = self._tree.index(item)
        if idx >= len(self._filtered_processes):
            self._hide_tooltip()
            return

        proc = self._filtered_processes[idx]
        self._show_tooltip(event, proc.command)

    def _show_tooltip(self, event, text: str):
        self._hide_tooltip()
        x = event.x_root + 10
        y = event.y_root + 10

        self._tooltip_window = tw = tk.Toplevel(self)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw, text=text, justify=tk.LEFT,
            background="#ffffe0", foreground="#000000",
            relief=tk.SOLID, borderwidth=1,
            font=("Menlo", 10), wraplength=600,
        )
        label.pack()

    def _hide_tooltip(self, _event=None):
        if self._tooltip_window:
            self._tooltip_window.destroy()
            self._tooltip_window = None


def _shorten(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
