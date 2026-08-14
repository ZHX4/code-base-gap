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


def _parse_sarif_safe(run: ToolRun, tool_name: str) -> tuple[ToolRun, list[Finding]]:
    if not run.stdout.lstrip().startswith("{"):
        return run, []
    try:
        return run, parse_sarif(run.stdout, tool_name)
    except (json.JSONDecodeError, ValueError) as exc:
        return ToolRun(run.metadata, run.exit_code, run.duration_ms, run.output_truncated, run.stdout, f"invalid SARIF output: {type(exc).__name__}"), []


def run_semgrep(root: Path, timeout_s: int = 300) -> tuple[ToolRun, list[Finding]]:
    run = run_tool("semgrep", ["scan", "--config", "auto", "--sarif", "--quiet", str(root)], root, timeout_s)
    return _parse_sarif_safe(run, "semgrep")


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
        if not report_text.lstrip().startswith("{"):
            return run, []
        try:
            return run, parse_sarif(report_text, "gitleaks")
        except (json.JSONDecodeError, ValueError) as exc:
            return ToolRun(run.metadata, run.exit_code, run.duration_ms, run.output_truncated, run.stdout, f"invalid Gitleaks SARIF output: {type(exc).__name__}"), []
    finally:
        path.unlink(missing_ok=True)


def run_trivy(root: Path, timeout_s: int = 300) -> tuple[ToolRun, list[Finding]]:
    run = run_tool("trivy", ["fs", "--scanners", "vuln,misconfig,secret", "--format", "sarif", str(root)], root, timeout_s)
    return _parse_sarif_safe(run, "trivy")


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
    if metadata.exit_code != 0 or metadata.metadata.version is None:
        failed = ToolRun(metadata.metadata, metadata.exit_code, metadata.duration_ms, metadata.output_truncated, metadata.stdout, "CodeQL version discovery failed")
        return failed, []
    discovered = ToolRun(metadata.metadata, metadata.exit_code, metadata.duration_ms, metadata.output_truncated, metadata.stdout, "Phase 5 CodeQL adapter is discovery-only; build/database creation is deferred to the sandbox phase")
    return discovered, []
