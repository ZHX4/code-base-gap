"""Command-line entry point for Phase 2."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import AuditInput
from .pipeline import run_phase2, write_result
from .source import SourceError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="code-base-gap",
        description="Run safe repository ingestion and reconnaissance without executing repository code.",
    )
    parser.add_argument("source", help="Local repository directory or public HTTPS GitHub repository")
    parser.add_argument("--ref", help="GitHub branch, tag, or commit to pin; omitted means the default branch")
    parser.add_argument("--output", type=Path, help="Write the JSON audit result to this file")
    parser.add_argument("--max-files", type=int, default=100_000)
    parser.add_argument("--max-file-bytes", type=int, default=2_000_000)
    parser.add_argument("--max-total-bytes", type=int, default=256_000_000)
    parser.add_argument("--max-archive-bytes", type=int, default=512_000_000)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = run_phase2(
            AuditInput(
                source=args.source,
                ref=args.ref,
                max_files=args.max_files,
                max_file_bytes=args.max_file_bytes,
                max_total_bytes=args.max_total_bytes,
                max_archive_bytes=args.max_archive_bytes,
            )
        )
    except (SourceError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    payload = result.to_dict()
    if args.output:
        write_result(result, args.output)
    else:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
