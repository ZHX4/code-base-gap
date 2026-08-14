"""Adapters for external deterministic analysis tools."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .models import Finding, ToolRun
from .runner import run_tool
from .sarif import parse_sarif

MAX_GITLEAKS_REPORT_BYTES = 20_000_000


def run_semgrep(root: Path, timeout_s: int = 300) -> tuple[ToolRun, list[Finding]]:
    run = run_tool("semgrep", ["scan", "--config", "auto", "--sarif", "--quiet", str(root)], root, timeout_s)
    return run, parse_sarif(run.stdout, "semgrep") if run.stdout.lstrip().startswith("{") else []


def run_gitleaks(root: Path, timeout_s: int = 300) -> tuple[ToolRun, list[Finding]]:
    fd, report_path = tempfile.mkstemp(prefix="cbg-gitleaks-", suffix=".sarif")
    os.close(fd)
    path = Path(report_path)
    try:
        path.unlink(missing_ok=True)
        run = run_tool("gitleaks", ["detect", "--source", str(root), "--no-git", "--report-format", "sarif", "--report-path", str(path)], root, timeout_s)
        report_text = ""
        if path.is_file():
            if path.stat().st_size <= MAX_GITLEAKS_REPORT_BYTES:
                report_text = path.read_text(encoding="utf-8", errors="replace")
            else:
                run = ToolRun(run.metadata, run.exit_code, run.duration_ms, True, run.stdout, "gitleaks SARIF report exceeded the adapter size limit")
        return run, parse_sarif(report_text, "gitleaks") if report_text.lstrip().startswith("{") else []
    finally:
        path.unlink(missing_ok=True)


def run_trivy(root: Path, timeout_s: int = 300) -> tuple[ToolRun, list[Finding]]:
    run = run_tool("trivy", ["fs", "--scanners", "vuln,misconfig,secret", "--format", "sarif", str(root)], root, timeout_s)
    return run, parse_sarif(run.stdout, "trivy") if run.stdout.lstrip().startswith("{") else []


def run_syft(root: Path, timeout_s: int = 180) -> tuple[ToolRun, dict]:
    run = run_tool("syft", [str(root), "-o", "json"], root, timeout_s)
    if not run.stdout.lstrip().startswith("{"):
        return run, {}
    try:
        return run, json.loads(run.stdout)
    except json.JSONDecodeError:
        return run, {}


def run_codeql(root: Path, languages: list[str] | None = None, timeout_s: int = 600) -> tuple[ToolRun, list[Finding]]:
    metadata = run_tool("codeql", ["version"], root, 10)
    if metadata.metadata.status == "unavailable":
        return metadata, []
    metadata = ToolRun(metadata.metadata, 0, metadata.duration_ms, False, metadata.stdout, "Phase 5 CodeQL adapter is discovery-only; build/database creation is deferred to the sandbox phase")
    return metadata, []
