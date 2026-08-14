#!/usr/bin/env python3
"""Validate the Phase 2 implementation package without executing repository code."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "code_base_gap" / "phase2"
SCHEMAS = ROOT / "spec" / "schemas"

REQUIRED_MODULES = {"__init__.py", "models.py", "filesystem.py", "source.py", "recon.py", "pipeline.py", "cli.py"}
REQUIRED_SCHEMAS = {"phase2-manifest.schema.json", "phase2-reconnaissance.schema.json"}


def validate_python() -> None:
    actual = {p.name for p in PKG.glob("*.py")}
    missing = REQUIRED_MODULES - actual
    assert not missing, f"missing Phase 2 modules: {sorted(missing)}"
    for path in PKG.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def validate_json() -> None:
    for name in REQUIRED_SCHEMAS:
        path = SCHEMAS / name
        assert path.is_file(), f"missing schema: {name}"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("$schema"), f"{name}: missing $schema"
        assert data.get("$id"), f"{name}: missing $id"


def validate_docs() -> None:
    doc = ROOT / "docs" / "phase-2" / "README.md"
    assert doc.is_file(), "missing Phase 2 documentation"
    text = doc.read_text(encoding="utf-8")
    for phrase in ("repository revision", "no build", "reconnaissance", "limitations"):
        assert phrase.lower() in text.lower(), f"Phase 2 documentation missing: {phrase}"


def main() -> int:
    validate_python()
    validate_json()
    validate_docs()
    print("Phase 2 structural validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
