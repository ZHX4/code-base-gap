#!/usr/bin/env python3
"""Validate Phase 3 source structure and machine-readable contracts."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "code_base_gap" / "phase3"
SCHEMA = ROOT / "spec" / "schemas" / "phase3-semantic-index.schema.json"
REQUIRED = {"__init__.py", "models.py", "parser.py", "extract.py", "indexer.py", "pipeline.py", "cli.py"}


def main() -> int:
    actual = {path.name for path in PKG.glob("*.py")}
    missing = REQUIRED - actual
    if missing:
        raise SystemExit(f"missing Phase 3 modules: {sorted(missing)}")
    for path in PKG.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    if not SCHEMA.is_file():
        raise SystemExit("missing Phase 3 semantic-index schema")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise SystemExit("Phase 3 schema has wrong JSON Schema dialect")
    if schema.get("$id") != "https://code-base-gap.dev/schema/phase3-semantic-index.schema.json":
        raise SystemExit("Phase 3 schema has wrong $id")
    expected = {"schema_version", "files", "symbol_count", "reference_count", "import_count", "endpoint_count", "query_count", "config_count", "integration_count", "test_count", "limitations", "parser_versions"}
    if not expected.issubset(set(schema.get("required", []))):
        raise SystemExit(f"Phase 3 schema missing required fields: {sorted(expected - set(schema.get('required', [])))}")
    symbol = schema.get("$defs", {}).get("symbol", {})
    if "name_span" not in symbol.get("required", []) or "name_span" not in symbol.get("properties", {}):
        raise SystemExit("Phase 3 symbol schema must expose name_span")
    print("Phase 3 structural validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
