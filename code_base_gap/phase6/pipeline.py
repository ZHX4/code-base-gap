"""Public Phase 6 reconstruction pipeline."""
from __future__ import annotations

from pathlib import Path

from .inputs import load_inputs
from .models import SystemModel
from .reconstruct import reconstruct_system


def reconstruct_system_from_files(reconnaissance: Path, graph: Path) -> SystemModel:
    inputs = load_inputs(reconnaissance, graph)
    graph_revision = inputs.graph.get("repository_revision")
    manifest_revision = inputs.reconnaissance["manifest"].get("repository_revision")
    if graph_revision and manifest_revision and graph_revision != manifest_revision:
        raise ValueError("Phase 2 and Phase 4 artifacts refer to different repository revisions")
    return reconstruct_system(inputs.reconnaissance, inputs.graph)


def reconstruct_system(reconnaissance: Path, graph: Path) -> SystemModel:
    return reconstruct_system_from_files(reconnaissance, graph)
