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
    if payload["manifest"].get("repository_revision") is None:
        raise ValueError("Phase 2 manifest must contain repository_revision")
    return payload


def load_phase4_graph(path: Path) -> dict[str, Any]:
    payload = _load(path)
    if payload.get("schema_version") != "phase4.program-knowledge-graph.v1":
        raise ValueError("unsupported Phase 4 graph schema version")
    if not isinstance(payload.get("nodes"), list) or not isinstance(payload.get("edges"), list):
        raise ValueError("Phase 4 graph must contain nodes and edges arrays")
    node_ids = {node.get("node_id") for node in payload["nodes"] if isinstance(node, dict)}
    for edge in payload["edges"]:
        if not isinstance(edge, dict) or edge.get("source") not in node_ids or edge.get("target") not in node_ids:
            raise ValueError("Phase 4 graph contains an orphan edge")
    return payload


def load_inputs(reconnaissance: Path, graph: Path) -> Phase6Inputs:
    return Phase6Inputs(load_phase2_result(reconnaissance), load_phase4_graph(graph))
