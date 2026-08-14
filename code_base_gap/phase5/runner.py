"""Fail-closed subprocess execution for trusted static-analysis binaries."""
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from .models import ToolMetadata, ToolRun

ALLOWED_TOOLS = {"semgrep", "gitleaks", "trivy", "syft", "codeql"}


def tool_path(name: str) -> str | None:
    if name not in ALLOWED_TOOLS:
        raise ValueError(f"tool is not allowlisted: {name}")
    return shutil.which(name)


def version(name: str, executable: str | None = None) -> str | None:
    executable = executable or tool_path(name)
    if not executable:
        return None
    try:
        result = subprocess.run([executable, "--version"], capture_output=True, text=True, timeout=5, check=False)
        text = (result.stdout or result.stderr).strip().splitlines()
        return text[0][:256] if text else None
    except (OSError, subprocess.SubprocessError):
        return None


def run_tool(name: str, args: list[str], cwd: Path, timeout_s: int = 120, max_output_bytes: int = 2_000_000) -> ToolRun:
    executable = tool_path(name)
    metadata = ToolMetadata(name, version(name, executable), "phase5-adapter.v1", "unavailable" if executable is None else "ready")
    if executable is None:
        return ToolRun(metadata, None, 0, False, "", "tool not installed")
    if not cwd.is_dir():
        raise ValueError("analysis workspace must be an existing directory")
    if any("\x00" in item for item in args):
        raise ValueError("tool arguments cannot contain NUL bytes")
    # No shell, no environment-provided commands, and only fixed adapter arguments reach this function.
    started = time.monotonic()
    try:
        result = subprocess.run(
            [executable, *args], cwd=cwd, shell=False, capture_output=True, text=True,
            timeout=timeout_s, check=False,
        )
        elapsed = int((time.monotonic() - started) * 1000)
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        truncated = len(stdout.encode()) > max_output_bytes or len(stderr.encode()) > max_output_bytes
        stdout = stdout.encode()[:max_output_bytes].decode("utf-8", "replace")
        stderr = stderr.encode()[:max_output_bytes].decode("utf-8", "replace")
        return ToolRun(metadata, result.returncode, elapsed, truncated, stdout, stderr)
    except subprocess.TimeoutExpired as exc:
        elapsed = int((time.monotonic() - started) * 1000)
        return ToolRun(metadata, None, elapsed, True, (exc.stdout or "")[-max_output_bytes:], "timeout")
    except OSError as exc:
        elapsed = int((time.monotonic() - started) * 1000)
        return ToolRun(metadata, None, elapsed, False, "", type(exc).__name__)
