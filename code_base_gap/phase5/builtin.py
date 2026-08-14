"""Deterministic repository-local checks that require no external binaries."""
from __future__ import annotations

import re
from pathlib import Path

from .fingerprint import finding_fingerprint, finding_id
from .models import Confidence, Evidence, Finding, Location, Severity

EXCLUDED_DIRS = {".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build", "out", "target", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".mypy_cache", ".tox", "coverage", "site-packages", ".next", ".nuxt", "cdk.out", "terraform.tfstate.d"}
SECRET_PATTERNS = [
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), Severity.HIGH),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"), Severity.HIGH),
    ("Private key material", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), Severity.CRITICAL),
    ("Generic credential assignment", re.compile(r"(?i)\b(?:password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['\"][^'\"]{12,}['\"]"), Severity.MEDIUM),
]
DANGEROUS_PATTERNS = [
    ("Python eval usage", re.compile(r"\beval\s*\("), "CWE-95", Severity.HIGH),
    ("Python exec usage", re.compile(r"\bexec\s*\("), "CWE-95", Severity.HIGH),
    ("JavaScript eval usage", re.compile(r"\beval\s*\("), "CWE-95", Severity.HIGH),
    ("Shell execution primitive", re.compile(r"\b(?:os\.system|subprocess\.(?:run|Popen|call)|child_process\.exec)\s*\("), "CWE-78", Severity.MEDIUM),
    ("Potential hardcoded HTTP secret in URL", re.compile(r"https?://[^\s:@]+:[^\s@]+@"), "CWE-798", Severity.HIGH),
]


def _iter_files(root: Path, max_file_bytes: int, max_files: int):
    seen = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink() or any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts[:-1]):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > max_file_bytes:
            continue
        if seen >= max_files:
            return
        seen += 1
        yield path


def _location(path: str, line: int, column: int) -> Location:
    return Location(path, line, column, line, column)


def _generic_finding(tool: str, title: str, description: str, category: str, severity: Severity, path: str, line: int, column: int, rule: str, cwe: str | None = None) -> Finding:
    fp = finding_fingerprint(tool, rule, path, line, title)
    location = _location(path, line, column)
    return Finding(
        finding_id=finding_id(fp), fingerprint=fp, title=title, description=description,
        category=category, severity=severity, confidence=Confidence.MEDIUM, source_tool=tool,
        location=location, evidence=(Evidence("pattern-match", tool, description, location, fp, {"rule": rule}),),
        cwe=(cwe,) if cwe else (),
    )


def scan_secrets(root: Path, max_file_bytes: int = 2_000_000, max_files: int = 100_000) -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_files(root, max_file_bytes, max_files):
        try: text = path.read_text(encoding="utf-8", errors="replace")
        except OSError: continue
        rel = path.relative_to(root).as_posix()
        for line_no, line in enumerate(text.splitlines(), 1):
            for title, pattern, severity in SECRET_PATTERNS:
                match = pattern.search(line)
                if not match: continue
                fp = finding_fingerprint("builtin-secrets", title, rel, line_no, title)
                loc = _location(rel, line_no, match.start() + 1)
                findings.append(Finding(
                    finding_id=finding_id(fp), fingerprint=fp, title=title,
                    description="Potential secret or credential material detected by deterministic pattern analysis.",
                    category="secrets", severity=severity, confidence=Confidence.MEDIUM, source_tool="builtin-secrets",
                    location=loc, evidence=(Evidence("pattern-match", "builtin-secrets", line.strip()[:500], loc, fp),),
                ))
    return findings


def scan_code_patterns(root: Path, max_file_bytes: int = 2_000_000, max_files: int = 100_000) -> list[Finding]:
    findings: list[Finding] = []
    allowed = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
    for path in _iter_files(root, max_file_bytes, max_files):
        if path.suffix.lower() not in allowed: continue
        try: text = path.read_text(encoding="utf-8", errors="replace")
        except OSError: continue
        rel = path.relative_to(root).as_posix()
        for line_no, line in enumerate(text.splitlines(), 1):
            for title, pattern, cwe, severity in DANGEROUS_PATTERNS:
                match = pattern.search(line)
                if match:
                    findings.append(_generic_finding("builtin-patterns", title, f"Potentially dangerous construct matched deterministic rule: {title}.", "security-pattern", severity, rel, line_no, match.start() + 1, title, cwe))
    return findings


def scan_infrastructure(root: Path, max_file_bytes: int = 2_000_000, max_files: int = 100_000) -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_files(root, max_file_bytes, max_files):
        rel = path.relative_to(root).as_posix().lower()
        if not (path.name.lower().startswith("dockerfile") or path.suffix.lower() in {".tf", ".tfvars", ".yaml", ".yml", ".json"}): continue
        try: text = path.read_text(encoding="utf-8", errors="replace")
        except OSError: continue
        for line_no, line in enumerate(text.splitlines(), 1):
            match = re.search(r"(?i)\b(?:privileged\s*[:=]\s*true|hostNetwork\s*[:=]\s*true|0\.0\.0\.0/0)\b", line)
            if match:
                findings.append(_generic_finding("builtin-iac", "Potentially permissive infrastructure configuration", "Infrastructure configuration contains a broad privilege/network exposure pattern.", "iac", Severity.MEDIUM, rel, line_no, match.start() + 1, "permissive-infrastructure"))
    return findings
