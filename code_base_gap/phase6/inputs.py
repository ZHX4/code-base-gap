"""Strict JSON loaders for Phase 2 reconnaissance and Phase 4 graphs."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Phase6Inputs:
    reconnaissance: dict[str, Any]
    graph: dict[str, Any]


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"input file does not exist: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON input: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"input must be a JSON object: {path}")
    return value


def load_phase2_result(path: Path) -> dict[str, Any]:
    payload = _load(path)
    if not isinstance(payload.get("manifest"), dict) or not isinstance(payload.get("reconnaissance"), dict):
        raise ValueError("Phase 2 input must contain manifest and reconnaissance objects")
    revision = payload["manifest"].get("repository_revision")
    if not isinstance(revision, str) or not revision:
        raise ValueError("Phase 2 manifest must contain repository_revision")
    return payload


def load_phase4_graph(path: Path) -> dict[str, Any]:
    payload = _load(path)
    if payload.get("schema_version") != "phase4.program-knowledge-graph.v1":
        raise ValueError("unsupported Phase 4 graph schema version")
    revision = payload.get("repository_revision")
    if not isinstance(revision, str) or not revision:
        raise ValueError("Phase 4 graph must contain repository_revision for Phase 6 reconstruction")
    nodes = payload.get("nodes")
    edges = payload.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValueError("Phase 4 graph must contain nodes and edges arrays")
    node_ids: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("node_id"), str) or not node["node_id"]:
            raise ValueError("Phase 4 graph contains an invalid node")
        node_id = node["node_id"]
        if node_id in node_ids:
            raise ValueError(f"Phase 4 graph contains duplicate node ID: {node_id}")
        node_ids.add(node_id)
    edge_ids: set[str] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            raise ValueError("Phase 4 graph contains an invalid edge")
        edge_id = edge.get("edge_id")
        if not isinstance(edge_id, str) or not edge_id:
            raise ValueError("Phase 4 graph contains an edge without a valid ID")
        if edge_id in edge_ids:
            raise ValueError(f"Phase 4 graph contains duplicate edge ID: {edge_id}")
        edge_ids.add(edge_id)
        if edge.get("source") not in node_ids or edge.get("target") not in node_ids:
            raise ValueError("Phase 4 graph contains an orphan edge")
    return payload


def load_inputs(reconnaissance: Path, graph: Path) -> Phase6Inputs:
    return Phase6Inputs(load_phase2_result(reconnaissance), load_phase4_graph(graph))
