"""Public Phase 3 pipeline entry points."""
from __future__ import annotations

import json
from pathlib import Path

from .indexer import build_semantic_index
from .models import SemanticIndex, SemanticIndexConfig


def run_phase3(
    root: str | Path,
    *,
    repository_revision: str | None = None,
    config: SemanticIndexConfig | None = None,
) -> SemanticIndex:
    return build_semantic_index(Path(root), config=config, repository_revision=repository_revision)


def write_semantic_index(index: SemanticIndex, output: str | Path) -> None:
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(index.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
