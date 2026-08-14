#!/usr/bin/env python3
"""Structural validation for Phase 6 modules and system-model contract."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "code_base_gap" / "phase6"
SCHEMA = ROOT / "spec" / "schemas" / "phase6-system-model.schema.json"
REQUIRED = {"__init__.py", "models.py", "inputs.py", "reconstruct.py", "pipeline.py", "cli.py"}
EXPECTED_DEFS = {"provenance", "evidence", "component", "entryPoint", "dataStore", "dependency", "boundary", "criticalPath", "signal"}
REQUIRED_TOP_LEVEL = {"schema_version", "repository_revision", "components", "entry_points", "data_stores", "external_dependencies", "trust_boundaries", "critical_paths", "signals", "limitations", "stats"}


def main() -> int:
    actual = {p.name for p in PKG.glob("*.py")}
    missing = REQUIRED - actual
    if missing:
        raise SystemExit(f"missing Phase 6 modules: {sorted(missing)}")
    for path in PKG.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise SystemExit("wrong Phase 6 JSON Schema dialect")
    if schema.get("$id") != "https://code-base-gap.dev/schema/phase6-system-model.schema.json":
        raise SystemExit("wrong Phase 6 schema id")
    if schema.get("properties", {}).get("schema_version", {}).get("const") != "phase6.system-model.v1":
        raise SystemExit("wrong Phase 6 schema version")
    if set(schema.get("required", [])) != REQUIRED_TOP_LEVEL:
        raise SystemExit("Phase 6 top-level required-field contract mismatch")
    if set(schema.get("$defs", {})) != EXPECTED_DEFS:
        raise SystemExit("Phase 6 definition contract mismatch")
    provenance = set(schema["$defs"]["provenance"]["enum"])
    if provenance != {"observed", "inferred", "unknown"}:
        raise SystemExit("provenance contract mismatch")
    for definition in EXPECTED_DEFS - {"provenance"}:
        if "properties" not in schema["$defs"][definition] or "required" not in schema["$defs"][definition]:
            raise SystemExit(f"Phase 6 definition lacks required machine-readable contract: {definition}")
    print("Phase 6 structural validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
