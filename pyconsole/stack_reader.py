import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field


@dataclass
class StackFrame:
    name: str
    filename: str
    line: int


@dataclass
class ThreadInfo:
    id: int
    name: str
    frames: list[StackFrame] = field(default_factory=list)

    @property
    def top_function(self) -> str:
        if self.frames:
            return self.frames[0].name
        return "<unknown>"


@dataclass
class DumpResult:
    threads: list[ThreadInfo]
    pid: int
    error: str | None = None


_INJECT_TEMPLATE = (
    "import sys,json,threading\\n"
    "frames=sys._current_frames()\\n"
    "id2name=dict((t.ident,t.name) for t in threading.enumerate())\\n"
    "result=[]\\n"
    "for tid,frame in frames.items():\\n"
    "    stack=[]\\n"
    "    f=frame\\n"
    "    while f:\\n"
    "        stack.append(dict(name=f.f_code.co_name,filename=f.f_code.co_filename,line=f.f_lineno))\\n"
    "        f=f.f_back\\n"
    "    result.append(dict(thread_id=tid,thread_name=id2name.get(tid,''),frames=stack))\\n"
    "open('OUTPUT_FILE','w').write(json.dumps(result))\\n"
)


def dump_stacks(pid: int) -> DumpResult:
    output_file = os.path.join(tempfile.gettempdir(), f"_pyconsole_dump_{pid}.json")

    script = _INJECT_TEMPLATE.replace("OUTPUT_FILE", output_file)

    lldb_commands = (
        f"process attach --pid {pid}\n"
        f'expr (void*)PyGILState_Ensure()\n'
        f'expr (int)PyRun_SimpleString("{script}")\n'
        f'expr (void)PyGILState_Release($0)\n'
        f'detach\n'
        f'quit\n'
    )

    try:
        result = subprocess.run(
            ["lldb", "--batch"],
            input=lldb_commands,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError:
        return DumpResult(
            threads=[], pid=pid,
            error="lldb not found. Install Xcode Command Line Tools."
        )
    except subprocess.TimeoutExpired:
        return DumpResult(
            threads=[], pid=pid,
            error="Timed out attaching to process"
        )

    if "error:" in result.stderr.lower() or "unable to attach" in result.stdout.lower():
        error = result.stderr.strip() or result.stdout.strip()
        return DumpResult(threads=[], pid=pid, error=error)

    if "attach failed" in result.stdout.lower():
        return DumpResult(
            threads=[], pid=pid,
            error=(
                "无法 attach 到进程 — 目标 Python 二进制有 hardened runtime 签名。\n"
                "仅 pyenv/homebrew 编译的 Python 进程可被 attach。\n"
                "系统 Python (/Library/Frameworks/...) 受 macOS 保护。"
            )
        )

    # Check if PyRun_SimpleString returned non-zero (Python error in target)
    if "(int) $1 = -1" in result.stdout:
        return DumpResult(
            threads=[], pid=pid,
            error="Failed to execute Python code in target process"
        )

    if not os.path.exists(output_file):
        return DumpResult(
            threads=[], pid=pid,
            error="No output from target process. It may not be a CPython process."
        )

    try:
        with open(output_file) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return DumpResult(threads=[], pid=pid, error=f"Failed to read dump: {e}")
    finally:
        try:
            os.unlink(output_file)
        except OSError:
            pass

    threads = []
    for thread_data in data:
        frames = [
            StackFrame(
                name=frame.get("name", "?"),
                filename=frame.get("filename", "?"),
                line=frame.get("line", 0),
            )
            for frame in thread_data.get("frames", [])
        ]
        threads.append(ThreadInfo(
            id=thread_data.get("thread_id", 0),
            name=thread_data.get("thread_name", ""),
            frames=frames,
        ))

    return DumpResult(threads=threads, pid=pid)
