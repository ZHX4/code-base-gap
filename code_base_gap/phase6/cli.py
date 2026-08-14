"""CLI for Phase 6 system reconstruction."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import reconstruct_system


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reconstruct a deterministic repository-level system model from Phase 2 and Phase 4 artifacts.")
    parser.add_argument("--reconnaissance", type=Path, required=True, help="Phase 2 result JSON")
    parser.add_argument("--graph", type=Path, required=True, help="Phase 4 program knowledge graph JSON")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    model = reconstruct_system(args.reconnaissance, args.graph)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(model.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
