import tkinter as tk
from tkinter import ttk

from pyconsole.process_list import PythonProcess
from pyconsole.ui.process_panel import ProcessPanel
from pyconsole.ui.thread_window import ThreadWindow


class App:
    def __init__(self):
        self._root = tk.Tk()
        self._root.title("PyConsole — Python Thread Inspector")
        self._root.geometry("600x500")
        self._build_ui()

    def _build_ui(self):
        self._process_panel = ProcessPanel(self._root, on_attach=self._on_attach)
        self._process_panel.pack(fill=tk.BOTH, expand=True)

        self._status_var = tk.StringVar(value="Double-click or select + Attach to inspect a process")
        status_bar = ttk.Label(
            self._root, textvariable=self._status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=2, pady=2)

    def _on_attach(self, process: PythonProcess):
        if not process.attachable:
            self._status_var.set(
                f"PID {process.pid}: hardened runtime, cannot attach"
            )
            return
        self._status_var.set(f"Attached to PID {process.pid}")
        ThreadWindow(self._root, process)

    def run(self):
        self._root.mainloop()
