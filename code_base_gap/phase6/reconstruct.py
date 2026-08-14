"""Deterministic reconstruction of a repository-level system model."""
from __future__ import annotations

import hashlib
import posixpath
import re
from collections import defaultdict
from typing import Any

from .models import (
    BoundaryKind,
    ComponentKind,
    CriticalPath,
    DataStore,
    EntryPoint,
    EvidenceRef,
    ExternalDependency,
    Provenance,
    ReconstructionSignal,
    SystemComponent,
    SystemModel,
    TrustBoundary,
)


def _id(kind: str, *parts: object) -> str:
    material = "\x1f".join([kind, *(str(p) for p in parts)])
    return f"{kind}:{hashlib.sha256(material.encode()).hexdigest()[:24]}"


def _e(source: str, subject: str, detail: str, provenance: Provenance) -> EvidenceRef:
    return EvidenceRef(source=source, subject=subject, detail=detail, provenance=provenance)


def _graph_maps(graph: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    nodes = {str(node["node_id"]): node for node in graph.get("nodes", [])}
    edges = list(graph.get("edges", []))
    outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
    incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        outgoing[str(edge["source"])].append(edge)
        incoming[str(edge["target"])].append(edge)
    return nodes, edges, outgoing, incoming


def _component_root(path: str, known_roots: list[str]) -> str:
    clean = path.strip("/")
    if not clean:
        return "."
    parts = clean.split("/")
    candidates = []
    for root in known_roots:
        root_clean = root.strip("/")
        if root_clean and (clean == root_clean or clean.startswith(root_clean + "/")):
            candidates.append(root_clean)
    if candidates:
        return sorted(candidates, key=lambda value: (-len(value), value))[0]
    if parts[0] in {"apps", "services", "packages", "libs", "modules", "components"} and len(parts) >= 2:
        return "/".join(parts[:2])
    if parts[0] in {"src", "server", "backend", "frontend", "api", "app", "infra", "infrastructure"}:
        return parts[0]
    return parts[0]


def _component_kind(root: str, path_count: int) -> ComponentKind:
    first = root.split("/", 1)[0]
    if first in {"infra", "infrastructure"}:
        return ComponentKind.INFRASTRUCTURE
    if first in {"packages", "libs", "modules", "components"}:
        return ComponentKind.LIBRARY
    if first in {"apps", "services"}:
        return ComponentKind.SERVICE
    if path_count > 0:
        return ComponentKind.APPLICATION
    return ComponentKind.UNKNOWN


def _file_path(node: dict[str, Any]) -> str | None:
    value = node.get("properties", {}).get("path") if isinstance(node.get("properties"), dict) else None
    return str(value) if value else None


def _node_kind(node: dict[str, Any]) -> str:
    return str(node.get("kind", "unknown"))


def reconstruct_system(recon: dict[str, Any], graph: dict[str, Any]) -> SystemModel:
    manifest = recon["manifest"]
    reconnaissance = recon["reconnaissance"]
    revision = str(manifest["repository_revision"])
    nodes, edges, outgoing, incoming = _graph_maps(graph)
    model = SystemModel(repository_revision=revision)

    file_nodes = [node for node in nodes.values() if _node_kind(node) == "file"]
    files_by_path = {_file_path(node): node for node in file_nodes if _file_path(node)}
    known_roots = list(reconnaissance.get("source_roots", []))

    files_by_root: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for path, node in files_by_path.items():
        files_by_root[_component_root(path, known_roots)].append((path, node))

    component_by_root: dict[str, str] = {}
    for root, entries in sorted(files_by_root.items()):
        component_id = _id("component", revision, root)
        component_by_root[root] = component_id
        languages = sorted({str(entry[1].get("properties", {}).get("language")) for entry in entries if entry[1].get("properties", {}).get("language")})
        frameworks = sorted(set(str(value) for value in reconnaissance.get("frameworks", [])))
        provenance = Provenance.OBSERVED if root in known_roots else Provenance.INFERRED
        evidence = [_e("phase2.reconnaissance", root, "source root explicitly reported by Phase 2", Provenance.OBSERVED)] if root in known_roots else [_e("phase4.graph", root, "component root inferred from file-path topology", Provenance.INFERRED)]
        model.components.append(SystemComponent(component_id, root, _component_kind(root, len(entries)), (root,), tuple(languages), tuple(frameworks), provenance, tuple(evidence)))

    file_to_component = {}
    for root, entries in files_by_root.items():
        for path, _ in entries:
            file_to_component[path] = component_by_root[root]

    endpoint_nodes = [node for node in nodes.values() if _node_kind(node) == "endpoint"]
    for node in endpoint_nodes:
        props = node.get("properties", {})
        file_path = None
        for edge in incoming.get(str(node["node_id"]), []):
            source = nodes.get(str(edge["source"]))
            if source and _node_kind(source) == "file":
                file_path = _file_path(source)
                break
        component_id = file_to_component.get(file_path or "")
        entry_id = _id("entry", revision, node["node_id"])
        model.entry_points.append(EntryPoint(
            entry_id,
            "http-endpoint",
            props.get("path"),
            props.get("method"),
            file_path,
            props.get("handler_hint"),
            component_id,
            Provenance.OBSERVED,
            (_e("phase4.graph", str(node["node_id"]), "endpoint node exposes an application entry point", Provenance.OBSERVED),),
        ))

    query_nodes = [node for node in nodes.values() if _node_kind(node) == "query"]
    store_groups: dict[tuple[str, str], dict[str, Any]] = {}
    for node in query_nodes:
        props = node.get("properties", {})
        text = str(props.get("text", ""))
        kind = str(props.get("query_kind", "unknown"))
        qkind = kind.lower()
        if any(token in text.lower() for token in ("postgres", "postgresql")):
            store_kind = "postgresql"
        elif "mysql" in text.lower():
            store_kind = "mysql"
        elif "sqlite" in text.lower():
            store_kind = "sqlite"
        elif "mongodb" in text.lower() or "mongoose" in text.lower():
            store_kind = "mongodb"
        else:
            store_kind = "database"
        owner_file = None
        for edge in incoming.get(str(node["node_id"]), []):
            source = nodes.get(str(edge["source"]))
            if source and _node_kind(source) == "file":
                owner_file = _file_path(source)
                break
            if source and _node_kind(source) == "symbol":
                path = source.get("properties", {}).get("path")
                if path:
                    owner_file = str(path)
                    break
        component_id = file_to_component.get(owner_file or "")
        key = (store_kind, component_id or "unknown")
        group = store_groups.setdefault(key, {"files": set(), "operations": set(), "components": set(), "nodes": []})
        if owner_file:
            group["files"].add(owner_file)
        group["operations"].add(qkind)
        if component_id:
            group["components"].add(component_id)
        group["nodes"].append(str(node["node_id"]))

    for (store_kind, component_id), group in sorted(store_groups.items()):
        name = f"{store_kind} datastore" if component_id == "unknown" else f"{store_kind} datastore ({component_id})"
        model.data_stores.append(DataStore(
            _id("datastore", revision, store_kind, component_id), store_kind, name,
            tuple(sorted(group["files"])), tuple(sorted(group["operations"])), tuple(sorted(group["components"])),
            Provenance.INFERRED,
            tuple(_e("phase4.graph", node_id, "query node grouped into a datastore signal", Provenance.OBSERVED) for node_id in sorted(group["nodes"])[:20]),
        ))

    integration_nodes = [node for node in nodes.values() if _node_kind(node) in {"integration", "external_module"}]
    dep_groups: dict[tuple[str, str], set[str]] = defaultdict(set)
    for node in integration_nodes:
        label = str(node.get("label", "unknown"))
        kind = _node_kind(node)
        consumers: set[str] = set()
        for edge in incoming.get(str(node["node_id"]), []):
            source = nodes.get(str(edge["source"]))
            if source and _node_kind(source) == "file":
                path = _file_path(source)
                if path and path in file_to_component:
                    consumers.add(file_to_component[path])
        dep_groups[(kind, label)].update(consumers)

    for (kind, label), consumers in sorted(dep_groups.items()):
        model.external_dependencies.append(ExternalDependency(
            _id("dependency", revision, kind, label), label, kind,
            tuple(sorted(consumers)), Provenance.OBSERVED,
            (_e("phase4.graph", label, "integration/external-module node is present in the program graph", Provenance.OBSERVED),),
        ))

    for entry in model.entry_points:
        component_ids = (entry.component_id,) if entry.component_id else ()
        model.trust_boundaries.append(TrustBoundary(
            _id("boundary", revision, "internet", entry.entry_point_id),
            BoundaryKind.INTERNET, "external HTTP ingress", component_ids, (entry.entry_point_id,),
            Provenance.INFERRED,
            (_e("phase4.graph", entry.entry_point_id, "HTTP endpoint is treated as an internet-facing ingress signal; deployment exposure is not proven", Provenance.INFERRED),),
        ))

    for dep in model.external_dependencies:
        consumers = dep.consuming_components
        if consumers:
            boundary_kind = BoundaryKind.EXTERNAL_SERVICE if dep.kind in {"integration", "external_module"} else BoundaryKind.UNKNOWN
            model.trust_boundaries.append(TrustBoundary(
                _id("boundary", revision, boundary_kind.value, dep.dependency_id),
                boundary_kind, dep.name, consumers, (), Provenance.INFERRED,
                (_e("phase4.graph", dep.dependency_id, "external integration/module forms a trust-boundary signal", Provenance.INFERRED),),
            ))

    for store in model.data_stores:
        model.trust_boundaries.append(TrustBoundary(
            _id("boundary", revision, "database", store.data_store_id),
            BoundaryKind.DATABASE, store.name, store.component_ids, (), Provenance.INFERRED,
            (_e("phase4.graph", store.data_store_id, "query activity indicates a data-store interaction; actual deployment topology is not proven", Provenance.INFERRED),),
        ))

    endpoint_by_file: dict[str, list[EntryPoint]] = defaultdict(list)
    for entry in model.entry_points:
        if entry.file_path:
            endpoint_by_file[entry.file_path].append(entry)

    query_by_file: dict[str, list[str]] = defaultdict(list)
    for node in query_nodes:
        for edge in incoming.get(str(node["node_id"]), []):
            source = nodes.get(str(edge["source"]))
            if source and _node_kind(source) == "file":
                path = _file_path(source)
                if path:
                    query_by_file[path].append(str(node["node_id"]))

    integration_by_file: dict[str, list[str]] = defaultdict(list)
    for node in integration_nodes:
        for edge in incoming.get(str(node["node_id"]), []):
            source = nodes.get(str(edge["source"]))
            if source and _node_kind(source) == "file":
                path = _file_path(source)
                if path:
                    integration_by_file[path].append(str(node["node_id"]))

    for entry in model.entry_points:
        if not entry.file_path:
            continue
        steps = [entry.entry_point_id]
        component_id = entry.component_id
        if component_id:
            steps.append(component_id)
        for query_id in sorted(set(query_by_file.get(entry.file_path, [])))[:8]:
            steps.append(query_id)
        for integration_id in sorted(set(integration_by_file.get(entry.file_path, [])))[:8]:
            steps.append(integration_id)
        if len(steps) > 1:
            model.critical_paths.append(CriticalPath(
                _id("path", revision, entry.entry_point_id), entry.entry_point_id, tuple(steps),
                "entry point to directly associated component/data/integration signals",
                Provenance.INFERRED,
                (_e("phase4.graph", entry.file_path, "steps are assembled from graph relationships sharing the entry-point file", Provenance.INFERRED),),
            ))

    for language, count in sorted((reconnaissance.get("languages") or {}).items()):
        model.signals.append(ReconstructionSignal(
            _id("signal", "language", language), "language", f"{language}:{count}", Provenance.OBSERVED,
            (_e("phase2.reconnaissance", language, f"Phase 2 detected {count} file(s)", Provenance.OBSERVED),),
        ))
    for framework in sorted(set(reconnaissance.get("frameworks", []))):
        model.signals.append(ReconstructionSignal(
            _id("signal", "framework", framework), "framework", framework, Provenance.OBSERVED,
            (_e("phase2.reconnaissance", framework, "Phase 2 framework detection", Provenance.OBSERVED),),
        ))
    for root in sorted(set(known_roots)):
        model.signals.append(ReconstructionSignal(
            _id("signal", "source-root", root), "source-root", root, Provenance.OBSERVED,
            (_e("phase2.reconnaissance", root, "Phase 2 source root", Provenance.OBSERVED),),
        ))
    for limitation in manifest.get("limitations", []):
        model.limitations.append(str(limitation))
    for limitation in reconnaissance.get("limitations", []):
        model.limitations.append(str(limitation))
    for limitation in graph.get("limitations", []):
        model.limitations.append(str(limitation))
    model.limitations.append("Trust-boundary and critical-path exposure is reconstructed deterministically from static evidence; runtime topology is not proven in Phase 6.")
    model.normalize()
    return model
