# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyConsole is a JConsole-like GUI tool for inspecting running Python processes. It lists Python processes, and for a selected process, displays per-thread stack traces by injecting code via `lldb`.

## Running

```bash
uv venv --python /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12
uv pip install -e .
.venv/bin/pyconsole
```

Requires a Python with tkinter compiled in. Homebrew/pyenv builds often lack `_tkinter`; use the python.org framework build.

## Dependencies

- `lldb` — ships with Xcode Command Line Tools. Used to attach to target processes and inject Python code that calls `sys._current_frames()`.
- `tkinter` — standard library GUI framework (must be compiled into the Python build).
- No pip dependencies — all imports are stdlib.

## Architecture

```
pyconsole/
├── main.py              # Entry point (registered as `pyconsole` console_script)
├── process_list.py      # Discovers running Python processes via `ps -eo`
├── stack_reader.py      # Attaches via lldb, injects Python code, reads JSON dump
└── ui/
    ├── app.py           # Main window, launches ThreadWindow on attach
    ├── process_panel.py # Process list Treeview with filter, tooltip, attach button
    └── thread_window.py # Per-process window: thread list + stack trace display
```

Data flow: user selects process → Attach → `ThreadWindow` opens → `stack_reader.dump_stacks(pid)` runs in background thread → attaches via lldb, calls `PyGILState_Ensure` + `PyRun_SimpleString` to execute `sys._current_frames()` inside the target → writes JSON to temp file → parsed into `DumpResult` → UI updated via `after(0, ...)`.
