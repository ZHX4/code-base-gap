"""Public Phase 4 pipeline entry points."""
from __future__ import annotations

import json
from pathlib import Path

from code_base_gap.phase3.models import SemanticIndex

from .builder import build_program_graph
from .models import ProgramKnowledgeGraph


def run_phase4(index: SemanticIndex) -> ProgramKnowledgeGraph:
    return build_program_graph(index)


def write_program_graph(graph: ProgramKnowledgeGraph, output: str | Path) -> None:
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(graph.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
