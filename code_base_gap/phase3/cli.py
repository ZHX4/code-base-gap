"""CLI for Phase 3 code parsing and semantic indexing."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import SemanticIndexConfig
from .pipeline import run_phase3, write_semantic_index


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="code-base-gap-parse",
        description="Parse supported repository files and build a machine-readable semantic index without executing repository code.",
    )
    parser.add_argument("source", type=Path, help="Local repository directory or extracted repository workspace")
    parser.add_argument("--output", type=Path, help="Write semantic index JSON to this file")
    parser.add_argument("--revision", help="Immutable repository revision to associate with the index")
    parser.add_argument("--max-files", type=int, default=100_000)
    parser.add_argument("--max-file-bytes", type=int, default=2_000_000)
    parser.add_argument("--max-total-bytes", type=int, default=256_000_000)
    parser.add_argument("--max-ast-nodes", type=int, default=200_000)
    parser.add_argument("--max-ast-depth", type=int, default=1_000)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = SemanticIndexConfig(
            max_files=args.max_files,
            max_file_bytes=args.max_file_bytes,
            max_total_bytes=args.max_total_bytes,
            max_ast_nodes_per_file=args.max_ast_nodes,
            max_ast_depth=args.max_ast_depth,
        )
        index = run_phase3(args.source, repository_revision=args.revision, config=config)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.output:
        write_semantic_index(index, args.output)
    else:
        json.dump(index.to_dict(), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
