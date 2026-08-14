"""CLI for Phase 5 deterministic analysis."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import run_phase5


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic analysis over an unexecuted repository workspace.")
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--revision", default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--no-external-tools", action="store_true")
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    report = run_phase5(args.workspace, args.revision, enable_external_tools=not args.no_external_tools, timeout_s=args.timeout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
