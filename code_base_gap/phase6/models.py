"""Canonical Phase 6 system-reconstruction domain models."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Provenance(StrEnum):
    OBSERVED = "observed"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


class ComponentKind(StrEnum):
    APPLICATION = "application"
    SERVICE = "service"
    PACKAGE = "package"
    LIBRARY = "library"
    INFRASTRUCTURE = "infrastructure"
    UNKNOWN = "unknown"


class BoundaryKind(StrEnum):
    INTERNET = "internet"
    INTERNAL = "internal"
    DATABASE = "database"
    EXTERNAL_SERVICE = "external-service"
    MESSAGE = "message"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EvidenceRef:
    source: str
    subject: str
    detail: str
    provenance: Provenance


@dataclass(frozen=True)
class SystemComponent:
    component_id: str
    name: str
    kind: ComponentKind
    root_paths: tuple[str, ...]
    languages: tuple[str, ...]
    frameworks: tuple[str, ...]
    provenance: Provenance
    evidence: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True)
class EntryPoint:
    entry_point_id: str
    kind: str
    path: str | None
    method: str | None
    file_path: str | None
    symbol_id: str | None
    component_id: str | None
    provenance: Provenance
    evidence: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True)
class DataStore:
    data_store_id: str
    kind: str
    name: str
    file_paths: tuple[str, ...]
    operations: tuple[str, ...]
    component_ids: tuple[str, ...]
    provenance: Provenance
    evidence: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True)
class ExternalDependency:
    dependency_id: str
    name: str
    kind: str
    consuming_components: tuple[str, ...]
    provenance: Provenance
    evidence: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True)
class TrustBoundary:
    boundary_id: str
    kind: BoundaryKind
    name: str
    component_ids: tuple[str, ...]
    entry_point_ids: tuple[str, ...]
    provenance: Provenance
    evidence: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True)
class CriticalPath:
    path_id: str
    entry_point_id: str
    steps: tuple[str, ...]
    reason: str
    provenance: Provenance
    evidence: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True)
class ReconstructionSignal:
    signal_id: str
    category: str
    value: str
    provenance: Provenance
    evidence: tuple[EvidenceRef, ...] = ()


@dataclass
class SystemModel:
    schema_version: str = "phase6.system-model.v1"
    repository_revision: str | None = None
    components: list[SystemComponent] = field(default_factory=list)
    entry_points: list[EntryPoint] = field(default_factory=list)
    data_stores: list[DataStore] = field(default_factory=list)
    external_dependencies: list[ExternalDependency] = field(default_factory=list)
    trust_boundaries: list[TrustBoundary] = field(default_factory=list)
    critical_paths: list[CriticalPath] = field(default_factory=list)
    signals: list[ReconstructionSignal] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    def normalize(self) -> None:
        self.components = sorted(self.components, key=lambda item: item.component_id)
        self.entry_points = sorted(self.entry_points, key=lambda item: item.entry_point_id)
        self.data_stores = sorted(self.data_stores, key=lambda item: item.data_store_id)
        self.external_dependencies = sorted(self.external_dependencies, key=lambda item: item.dependency_id)
        self.trust_boundaries = sorted(self.trust_boundaries, key=lambda item: item.boundary_id)
        self.critical_paths = sorted(self.critical_paths, key=lambda item: item.path_id)
        self.signals = sorted(self.signals, key=lambda item: item.signal_id)
        self.limitations = sorted(set(self.limitations))
        self.stats = {
            "components": len(self.components),
            "entry_points": len(self.entry_points),
            "data_stores": len(self.data_stores),
            "external_dependencies": len(self.external_dependencies),
            "trust_boundaries": len(self.trust_boundaries),
            "critical_paths": len(self.critical_paths),
            "signals": len(self.signals),
        }
        self.validate()

    def validate(self) -> None:
        component_ids = {item.component_id for item in self.components}
        entry_ids = {item.entry_point_id for item in self.entry_points}
        for entry in self.entry_points:
            if entry.component_id is not None and entry.component_id not in component_ids:
                raise ValueError(f"entry point references unknown component: {entry.component_id}")
        for store in self.data_stores:
            if not set(store.component_ids).issubset(component_ids):
                raise ValueError(f"data store references unknown component: {store.data_store_id}")
        for dep in self.external_dependencies:
            if not set(dep.consuming_components).issubset(component_ids):
                raise ValueError(f"dependency references unknown component: {dep.dependency_id}")
        for boundary in self.trust_boundaries:
            if not set(boundary.component_ids).issubset(component_ids):
                raise ValueError(f"boundary references unknown component: {boundary.boundary_id}")
            if not set(boundary.entry_point_ids).issubset(entry_ids):
                raise ValueError(f"boundary references unknown entry point: {boundary.boundary_id}")
        for path in self.critical_paths:
            if path.entry_point_id not in entry_ids:
                raise ValueError(f"critical path references unknown entry point: {path.path_id}")

    def to_dict(self) -> dict[str, Any]:
        self.normalize()
        return asdict(self)
