import threading
import tkinter as tk
from tkinter import ttk

from pyconsole.process_list import PythonProcess
from pyconsole.stack_reader import DumpResult, ThreadInfo, dump_stacks


class ThreadWindow(tk.Toplevel):
    def __init__(self, master, process: PythonProcess):
        super().__init__(master)
        self._process = process
        self._threads: list[ThreadInfo] = []

        self.title(f"PyConsole — PID {process.pid}")
        self.attributes("-topmost", True)
        self._build_ui()
        self._refresh()
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=4, pady=4)

        ttk.Label(
            toolbar,
            text=f"PID: {self._process.pid}  PPID: {self._process.ppid}",
            font=("Menlo", 11),
        ).pack(side=tk.LEFT)

        ttk.Button(toolbar, text="Refresh Threads", command=self._refresh).pack(side=tk.RIGHT)

        self._status_var = tk.StringVar(value="Attaching...")
        ttk.Label(toolbar, textvariable=self._status_var).pack(side=tk.RIGHT, padx=10)

        paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Thread list (top)
        thread_frame = ttk.Frame(paned)
        columns = ("id", "name", "function")
        self._thread_tree = ttk.Treeview(
            thread_frame, columns=columns, show="headings",
            selectmode="browse", height=8
        )
        self._thread_tree.heading("id", text="Thread ID")
        self._thread_tree.heading("name", text="Name")
        self._thread_tree.heading("function", text="Top Function")
        self._thread_tree.column("id", width=140, minwidth=100)
        self._thread_tree.column("name", width=150, minwidth=80)
        self._thread_tree.column("function", width=250, minwidth=100)

        thread_scroll = ttk.Scrollbar(
            thread_frame, orient=tk.VERTICAL, command=self._thread_tree.yview
        )
        self._thread_tree.configure(yscrollcommand=thread_scroll.set)
        self._thread_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        thread_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._thread_tree.bind("<<TreeviewSelect>>", self._on_thread_select)

        # Stack trace (bottom)
        stack_frame = ttk.Frame(paned)
        self._stack_text = tk.Text(
            stack_frame, wrap=tk.NONE, font=("Menlo", 11),
            state=tk.DISABLED, bg="#1e1e1e", fg="#d4d4d4",
            insertbackground="#d4d4d4"
        )
        text_scroll_y = ttk.Scrollbar(
            stack_frame, orient=tk.VERTICAL, command=self._stack_text.yview
        )
        text_scroll_x = ttk.Scrollbar(
            stack_frame, orient=tk.HORIZONTAL, command=self._stack_text.xview
        )
        self._stack_text.configure(
            yscrollcommand=text_scroll_y.set,
            xscrollcommand=text_scroll_x.set,
        )
        text_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        text_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self._stack_text.pack(fill=tk.BOTH, expand=True)

        self._stack_text.tag_configure("filename", foreground="#569cd6")
        self._stack_text.tag_configure("lineno", foreground="#b5cea8")
        self._stack_text.tag_configure("funcname", foreground="#dcdcaa")

        paned.add(thread_frame, weight=1)
        paned.add(stack_frame, weight=2)

    def _refresh(self):
        self._status_var.set("Reading...")
        self.update_idletasks()

        def _do():
            result = dump_stacks(self._process.pid)
            self.after(0, lambda: self._show_dump(result))

        threading.Thread(target=_do, daemon=True).start()

    def _show_dump(self, result: DumpResult):
        self._thread_tree.delete(*self._thread_tree.get_children())
        self._set_stack_text("")

        if result.error:
            self._status_var.set("Error")
            self._set_stack_text(f"Error: {result.error}")
            return

        self._threads = result.threads
        self._status_var.set(f"{len(result.threads)} thread(s)")

        for thread in result.threads:
            name = thread.name or f"Thread-{thread.id}"
            self._thread_tree.insert(
                "", tk.END,
                values=(thread.id, name, thread.top_function)
            )

        if result.threads:
            first = self._thread_tree.get_children()[0]
            self._thread_tree.selection_set(first)
            self._show_thread_stack(result.threads[0])

    def _on_thread_select(self, _event):
        selection = self._thread_tree.selection()
        if not selection:
            return
        idx = self._thread_tree.index(selection[0])
        if idx < len(self._threads):
            self._show_thread_stack(self._threads[idx])

    def _show_thread_stack(self, thread: ThreadInfo):
        self._stack_text.configure(state=tk.NORMAL)
        self._stack_text.delete("1.0", tk.END)

        name = thread.name or f"Thread-{thread.id}"
        self._stack_text.insert(tk.END, f'"{name}" tid={thread.id}\n\n')

        for frame in thread.frames:
            self._stack_text.insert(tk.END, "  ")
            self._stack_text.insert(tk.END, frame.filename, "filename")
            self._stack_text.insert(tk.END, ":")
            self._stack_text.insert(tk.END, str(frame.line), "lineno")
            self._stack_text.insert(tk.END, " in ")
            self._stack_text.insert(tk.END, frame.name, "funcname")
            self._stack_text.insert(tk.END, "\n")

        self._stack_text.configure(state=tk.DISABLED)

    def _set_stack_text(self, text: str):
        self._stack_text.configure(state=tk.NORMAL)
        self._stack_text.delete("1.0", tk.END)
        self._stack_text.insert("1.0", text)
        self._stack_text.configure(state=tk.DISABLED)
