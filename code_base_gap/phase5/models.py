"""Canonical finding and scan-report models for Phase 5."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    UNKNOWN = "unknown"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Location:
    path: str
    start_line: int | None = None
    start_column: int | None = None
    end_line: int | None = None
    end_column: int | None = None

    def __post_init__(self) -> None:
        normalized = self.path.replace("\\", "/")
        first = normalized.split("/", 1)[0]
        absolute_drive = len(first) == 2 and first[1] == ":" and first[0].isalpha()
        uri_scheme = normalized.lower().startswith(("file:", "http:", "https:")) or "://" in normalized
        if not self.path or normalized.startswith("/") or normalized.startswith("\\") or absolute_drive or uri_scheme or "\x00" in self.path or any(part == ".." for part in normalized.split("/")):
            raise ValueError("finding location must be a repository-relative path")
        for name, value in (("start_line", self.start_line), ("start_column", self.start_column), ("end_line", self.end_line), ("end_column", self.end_column)):
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive")


@dataclass(frozen=True)
class Evidence:
    kind: str
    source: str
    summary: str
    location: Location | None = None
    fingerprint: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def key(self) -> tuple[Any, ...]:
        loc = None if self.location is None else (self.location.path, self.location.start_line, self.location.start_column, self.location.end_line, self.location.end_column)
        return (self.kind, self.source, self.fingerprint, loc, self.summary)


@dataclass(frozen=True)
class ToolMetadata:
    name: str
    version: str | None
    adapter_version: str
    status: str


@dataclass(frozen=True)
class Finding:
    finding_id: str
    fingerprint: str
    title: str
    description: str
    category: str
    severity: Severity
    confidence: Confidence
    source_tool: str
    location: Location | None
    evidence: tuple[Evidence, ...] = ()
    cwe: tuple[str, ...] = ()
    cve: tuple[str, ...] = ()
    references: tuple[str, ...] = ()
    fix_hint: str | None = None
    verified: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ToolRun:
    metadata: ToolMetadata
    exit_code: int | None
    duration_ms: int
    output_truncated: bool
    stdout: str = ""
    stderr: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"metadata": asdict(self.metadata), "exit_code": self.exit_code, "duration_ms": self.duration_ms, "output_truncated": self.output_truncated}


@dataclass
class ScanReport:
    schema_version: str = "phase5.deterministic-scan.v1"
    repository_revision: str | None = None
    findings: list[Finding] = field(default_factory=list)
    tool_runs: list[ToolRun] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    def normalize(self) -> None:
        by_fingerprint: dict[str, Finding] = {}
        rank = {Severity.CRITICAL: 5, Severity.HIGH: 4, Severity.MEDIUM: 3, Severity.LOW: 2, Severity.INFO: 1, Severity.UNKNOWN: 0}
        for finding in self.findings:
            existing = by_fingerprint.get(finding.fingerprint)
            if existing is None:
                by_fingerprint[finding.fingerprint] = finding
                continue
            evidence_map = {item.key(): item for item in (*existing.evidence, *finding.evidence)}
            evidence = tuple(evidence_map[key] for key in sorted(evidence_map, key=str))
            chosen = finding if rank[finding.severity] > rank[existing.severity] else existing
            by_fingerprint[finding.fingerprint] = Finding(
                finding_id=chosen.finding_id, fingerprint=chosen.fingerprint, title=chosen.title, description=chosen.description,
                category=chosen.category, severity=chosen.severity, confidence=chosen.confidence, source_tool=chosen.source_tool,
                location=chosen.location, evidence=evidence, cwe=chosen.cwe, cve=chosen.cve, references=chosen.references,
                fix_hint=chosen.fix_hint, verified=chosen.verified, metadata=chosen.metadata,
            )
        self.findings = sorted(by_fingerprint.values(), key=lambda f: (-rank[f.severity], f.fingerprint))
        self.limitations = sorted(set(self.limitations))
        counts = {severity.value: 0 for severity in Severity}
        for finding in self.findings:
            counts[finding.severity.value] += 1
        counts["findings"] = len(self.findings)
        counts["tool_runs"] = len(self.tool_runs)
        counts["artifacts"] = len(self.artifacts)
        self.stats = counts

    def to_dict(self) -> dict[str, Any]:
        self.normalize()
        return {"schema_version": self.schema_version, "repository_revision": self.repository_revision, "findings": [f.to_dict() for f in self.findings], "tool_runs": [r.to_dict() for r in self.tool_runs], "artifacts": self.artifacts, "limitations": list(self.limitations), "stats": dict(self.stats)}
