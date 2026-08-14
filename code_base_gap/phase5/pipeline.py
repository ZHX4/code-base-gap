"""Phase 5 orchestration over an already-ingested analysis workspace."""
from __future__ import annotations

from pathlib import Path

from .adapters import run_codeql, run_gitleaks, run_semgrep, run_syft, run_trivy
from .builtin import scan_code_patterns, scan_infrastructure, scan_secrets
from .models import ScanReport


def run_phase5(
    root: Path,
    repository_revision: str | None = None,
    *,
    enable_external_tools: bool = True,
    timeout_s: int = 300,
    max_file_bytes: int = 2_000_000,
) -> ScanReport:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("Phase 5 workspace must be a directory")

    report = ScanReport(repository_revision=repository_revision)
    report.findings.extend(scan_secrets(root, max_file_bytes))
    report.findings.extend(scan_code_patterns(root, max_file_bytes))
    report.findings.extend(scan_infrastructure(root))

    if not enable_external_tools:
        report.limitations.append("external analyzers disabled by profile")
    else:
        adapters = (
            ("semgrep", lambda: run_semgrep(root, timeout_s)),
            ("gitleaks", lambda: run_gitleaks(root, timeout_s)),
            ("trivy", lambda: run_trivy(root, timeout_s)),
        )
        for name, action in adapters:
            run, findings = action()
            report.tool_runs.append(run)
            report.findings.extend(findings)
            if run.metadata.status == "unavailable":
                report.limitations.append(f"{name} is not installed; adapter produced no tool findings")
            elif run.exit_code not in (0, 1):
                report.limitations.append(f"{name} exited with status {run.exit_code}; output may be incomplete")
            if run.output_truncated:
                report.limitations.append(f"{name} output was truncated")

        codeql_run, codeql_findings = run_codeql(root, timeout_s=timeout_s * 2)
        report.tool_runs.append(codeql_run)
        report.findings.extend(codeql_findings)
        report.limitations.append("CodeQL database creation/build execution is deferred to Phase 18 sandbox execution")

        syft_run, sbom = run_syft(root, timeout_s=max(60, timeout_s // 2))
        report.tool_runs.append(syft_run)
        if syft_run.metadata.status == "unavailable":
            report.limitations.append("syft is not installed; SBOM was not generated")
        elif not sbom:
            report.limitations.append("syft did not return a parseable SBOM")

    report.normalize()
    return report
