"""Domain models for Phase 2 repository ingestion and reconnaissance."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuditInput:
    source: str
    ref: str | None = None
    max_files: int = 100_000
    max_file_bytes: int = 2_000_000
    max_total_bytes: int = 256_000_000
    max_archive_bytes: int = 512_000_000


@dataclass(frozen=True)
class FileEntry:
    path: str
    size_bytes: int
    extension: str
    language: str | None
    kind: str
    is_test: bool
    is_generated: bool
    is_config: bool
    is_documentation: bool
    is_symlink: bool


@dataclass
class AuditManifest:
    source: str
    requested_ref: str | None
    repository_revision: str
    source_kind: str
    workspace: str
    files: list[FileEntry] = field(default_factory=list)
    exclusions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)
    repository_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["files"] = [asdict(item) for item in self.files]
        return value


@dataclass
class ReconnaissanceReport:
    languages: dict[str, int] = field(default_factory=dict)
    frameworks: list[str] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)
    build_systems: list[str] = field(default_factory=list)
    test_frameworks: list[str] = field(default_factory=list)
    cicd: list[str] = field(default_factory=list)
    deployment: list[str] = field(default_factory=list)
    source_roots: list[str] = field(default_factory=list)
    likely_entry_points: list[str] = field(default_factory=list)
    configuration_files: list[str] = field(default_factory=list)
    documentation_files: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Phase2Result:
    manifest: AuditManifest
    reconnaissance: ReconnaissanceReport

    def to_dict(self) -> dict[str, Any]:
        return {"manifest": self.manifest.to_dict(), "reconnaissance": self.reconnaissance.to_dict()}
