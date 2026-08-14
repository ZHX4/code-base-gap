#!/usr/bin/env python3
"""Compatibility wrapper for the Phase 2 filesystem inventory implementation."""
from __future__ import annotations

import argparse
from pathlib import Path

from code_base_gap.phase2.filesystem import inventory
from code_base_gap.phase2.pipeline import _stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory a repository without executing it.")
    parser.add_argument("root", type=Path)
    parser.add_argument("--max-files", type=int, default=100_000)
    parser.add_argument("--max-file-bytes", type=int, default=2_000_000)
    parser.add_argument("--max-total-bytes", type=int, default=256_000_000)
    args = parser.parse_args()
    files, exclusions, limitations = inventory(args.root, args.max_files, args.max_file_bytes, args.max_total_bytes)
    import json
    print(json.dumps({"files": [item.__dict__ for item in files], "exclusions": exclusions, "limitations": limitations, "stats": _stats(files)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
