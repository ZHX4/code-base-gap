#!/usr/bin/env python3
"""Structural validation for Phase 4 modules and graph contract."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "code_base_gap" / "phase4"
SCHEMA = ROOT / "spec" / "schemas" / "phase4-program-knowledge-graph.schema.json"
REQUIRED = {"__init__.py", "models.py", "ids.py", "resolver.py", "builder.py", "loader.py", "query.py", "pipeline.py", "cli.py"}
EXPECTED_NODE_KINDS = {"repository", "file", "symbol", "module", "endpoint", "query", "config", "integration", "test", "external_module"}
EXPECTED_EDGE_KINDS = {"CONTAINS", "DECLARES", "IMPORTS", "EXPORTS", "RESOLVES_TO", "EXPOSES", "EXECUTES_QUERY", "USES_CONFIG", "INTEGRATES_WITH", "TESTS", "LOCATED_IN"}


def main() -> int:
    actual = {path.name for path in PKG.glob("*.py")}
    missing = REQUIRED - actual
    if missing:
        raise SystemExit(f"missing Phase 4 modules: {sorted(missing)}")
    for path in PKG.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise SystemExit("Phase 4 schema has wrong JSON Schema dialect")
    if schema.get("$id") != "https://code-base-gap.dev/schema/phase4-program-knowledge-graph.schema.json":
        raise SystemExit("Phase 4 schema has wrong $id")

    node_enum = set(schema["$defs"]["node"]["properties"]["kind"]["enum"])
    edge_enum = set(schema["$defs"]["edge"]["properties"]["kind"]["enum"])
    if node_enum != EXPECTED_NODE_KINDS:
        raise SystemExit(f"Phase 4 node-kind contract mismatch: {sorted(node_enum ^ EXPECTED_NODE_KINDS)}")
    if edge_enum != EXPECTED_EDGE_KINDS:
        raise SystemExit(f"Phase 4 edge-kind contract mismatch: {sorted(edge_enum ^ EXPECTED_EDGE_KINDS)}")

    print("Phase 4 structural validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
