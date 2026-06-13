# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyConsole is a JConsole-like GUI tool for inspecting running Python processes. It lists Python processes, and for a selected process, displays per-thread stack traces by injecting code via `lldb`.

## Running

```bash
/Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python run.py
```

No sudo needed — lldb has the entitlements to attach to user-owned processes on macOS (unlike py-spy which is blocked by SIP).

## Dependencies

- `lldb` — ships with Xcode Command Line Tools. Used to attach to target processes and inject Python code that calls `sys._current_frames()`.
- `tkinter` — standard library GUI framework (must be compiled into the Python build; the pyenv 3.11 on this machine lacks it).

## Architecture

```
pyconsole/
├── main.py              # Entry point
├── process_list.py      # Discovers running Python processes via `ps aux`
├── stack_reader.py      # Attaches via lldb, injects Python code, reads JSON dump
└── ui/
    ├── app.py           # Main window, wires panels together
    ├── process_panel.py # Left panel: process list Treeview with refresh
    └── stack_panel.py   # Right panel: thread list + stack trace Text widget
```

The UI uses a horizontal PanedWindow: process list on the left, thread inspector on the right. The right pane is a vertical split: thread Treeview (top) and syntax-highlighted stack trace (bottom).

Data flow: user selects process → clicks "Dump Stacks" → `stack_reader.dump_stacks(pid)` attaches via lldb, calls `PyGILState_Ensure` + `PyRun_SimpleString` to execute `sys._current_frames()` inside the target, writes JSON to a temp file → parsed into `DumpResult` → `StackPanel.show_dump()` renders it.
