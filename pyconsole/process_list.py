import os
import subprocess
from dataclasses import dataclass


@dataclass
class PythonProcess:
    pid: int
    ppid: int
    command: str
    user: str
    attachable: bool = True


def list_python_processes() -> list[PythonProcess]:
    result = subprocess.run(
        ["ps", "-eo", "user,pid,ppid,command"],
        capture_output=True, text=True
    )
    processes = []
    current_pid = os.getpid()

    for line in result.stdout.splitlines()[1:]:
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue

        user = parts[0]
        pid = int(parts[1])
        ppid = int(parts[2])
        command = parts[3]

        if pid == current_pid:
            continue

        lower_cmd = command.lower()
        if "python" not in lower_cmd:
            continue

        if any(skip in command for skip in [
            "pylance", "/pet ", "pydevd.py"
        ]):
            continue

        processes.append(PythonProcess(
            pid=pid,
            ppid=ppid,
            command=command,
            user=user,
            attachable=_is_likely_attachable(command),
        ))

    return processes


_HARDENED_PATHS = [
    "/usr/bin/python",
    "/System/",
]


def _is_likely_attachable(command: str) -> bool:
    return not any(p in command for p in _HARDENED_PATHS)
