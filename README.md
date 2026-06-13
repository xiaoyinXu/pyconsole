# PyConsole

A JConsole-like GUI tool for inspecting running Python processes. Select a Python process, attach to it, and view per-thread stack traces — all without instrumenting the target process.

![Python](https://img.shields.io/badge/python-3.10+-blue)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)

## Features

- **Process Discovery** — Lists all running Python processes with PID, PPID, and command
- **Keyword Filter** — Search/filter processes by command content
- **Attach & Inspect** — Attach to a process and view all thread stack traces in a new window
- **Manual Refresh** — Re-read thread stacks at any time without restarting
- **Non-blocking** — Stack reading runs in background threads, UI stays responsive
- **Tooltip** — Hover over truncated commands to see the full command line
- **Hardened Runtime Detection** — Marks processes that cannot be attached (macOS SIP)

## How It Works

PyConsole uses `lldb` to attach to a target Python process, acquires the GIL via `PyGILState_Ensure()`, then injects a small Python snippet that calls `sys._current_frames()` to capture all thread stacks. Results are written to a temp file as JSON, which the GUI reads and displays.

This approach requires no instrumentation of the target process — it works on any running CPython process that your user account owns.

## Requirements

- macOS (uses `lldb` which ships with Xcode Command Line Tools)
- Python 3.10+ with `tkinter` compiled in
- Developer mode enabled: `sudo DevToolsSecurity -enable`

> **Note:** The pyenv-installed Python on this machine lacks `_tkinter`. Use the system Python 3.12 to run the GUI.

## Usage

```bash
/Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python run.py
```

1. The main window shows all running Python processes
2. Use the filter box to search by keyword
3. Double-click a process (or select + click "Attach")
4. A new window opens showing all threads and their stack traces
5. Click "Refresh Threads" to update the stacks

## Limitations

- **Hardened Runtime**: System Python binaries signed with hardened runtime cannot be attached unless re-signed with ad-hoc signature (see below)
- **macOS only**: Uses `lldb` for process attachment; Linux/Windows not yet supported
- **Briefly pauses target**: The target process is stopped for a few milliseconds during stack capture

### Removing Hardened Runtime (if needed)

```bash
codesign -d --entitlements - /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 --xml > /tmp/ent.plist
sudo codesign -f -s - --entitlements /tmp/ent.plist /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12
```

## Project Structure

```
pyconsole/
├── main.py              # Entry point
├── process_list.py      # Discovers Python processes via ps
├── stack_reader.py      # Attaches via lldb, injects code, reads JSON dump
└── ui/
    ├── app.py           # Main window
    ├── process_panel.py # Process list with filter and tooltip
    └── thread_window.py # Per-process thread inspector window
```

## License

MIT
