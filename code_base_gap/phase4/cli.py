"""CLI for Phase 4 program knowledge graph construction."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from code_base_gap.phase3.models import SemanticIndex

from .pipeline import run_phase4, write_program_graph


def _load_index(path: Path) -> SemanticIndex:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "phase3.semantic-index.v1":
        raise ValueError("input is not a Phase 3 semantic index")
    # Keep the CLI format-compatible without reconstructing parser-specific classes.
    from code_base_gap.phase4.loader import semantic_index_from_dict
    return semantic_index_from_dict(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="code-base-gap-graph",
        description="Build a deterministic program knowledge graph from a Phase 3 semantic index.",
    )
    parser.add_argument("semantic_index", type=Path, help="Phase 3 semantic-index JSON")
    parser.add_argument("--output", type=Path, required=True, help="Output graph JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        graph = run_phase4(_load_index(args.semantic_index))
        write_program_graph(graph, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
