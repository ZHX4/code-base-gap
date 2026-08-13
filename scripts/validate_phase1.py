#!/usr/bin/env python3
"""Validate the Phase 1 specification package using only the Python standard library."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "docs" / "phase-1"
SCHEMAS = ROOT / "spec" / "schemas"
STATE_MACHINE = ROOT / "spec" / "audit-state-machine.json"

REQUIRED_DOCS = {
    "README.md",
    "product-definition.md",
    "architecture.md",
    "architecture-decisions.md",
    "audit-state-machine.md",
    "contracts.md",
    "threat-model.md",
    "evaluation.md",
    "definition-of-done.md",
}

REQUIRED_SCHEMAS = {
    "audit.schema.json",
    "audit-profile.schema.json",
    "audit-result.schema.json",
    "audit-state-machine.schema.json",
    "agent-run.schema.json",
    "checkpoint.schema.json",
    "coverage.schema.json",
    "evidence.schema.json",
    "finding.schema.json",
    "hypothesis.schema.json",
    "invariant.schema.json",
    "location.schema.json",
    "observation.schema.json",
    "tool-invocation.schema.json",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: top-level JSON value must be an object")
    return value


def assert_no_stale_typo() -> None:
    for path in list(PHASE1.glob("*.md")) + list(SCHEMAS.glob("*.json")):
        text = path.read_text(encoding="utf-8")
        assert "aud_it_summary" not in text, f"stale audit result typo in {path}"


def validate_json_files() -> None:
    paths = sorted(SCHEMAS.glob("*.json")) + [STATE_MACHINE]
    assert paths, "no Phase 1 JSON artifacts found"
    for path in paths:
        data = load_json(path)
        assert "$schema" in data, f"{path}: missing $schema"
        if path.parent == SCHEMAS:
            assert "$id" in data, f"{path}: missing $id"
            assert "title" in data, f"{path}: missing title"


def validate_schema_inventory() -> None:
    actual = {path.name for path in SCHEMAS.glob("*.json")}
    missing = REQUIRED_SCHEMAS - actual
    assert not missing, f"missing schemas: {sorted(missing)}"


def validate_relative_refs() -> None:
    for path in SCHEMAS.glob("*.json"):
        data = load_json(path)

        def walk(value: object) -> None:
            if isinstance(value, dict):
                ref = value.get("$ref")
                if isinstance(ref, str) and ref.startswith("./"):
                    target = (path.parent / ref).resolve()
                    assert target.exists(), f"{path}: broken relative $ref {ref}"
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(data)


def validate_state_machine() -> None:
    machine = load_json(STATE_MACHINE)
    states = machine["states"]
    terminal = set(machine["terminal_states"])

    assert isinstance(states, dict) and states, "state machine must contain states"
    assert all(state in states for state in terminal), "terminal state missing from state map"

    for state, definition in states.items():
        transitions = definition["transitions"]
        assert all(target in states for target in transitions), f"{state}: unknown transition target"
        assert definition["terminal"] == (state in terminal), f"{state}: terminal flag mismatch"
        if definition["terminal"]:
            assert transitions == [], f"{state}: terminal state must have no transitions"

    assert set(states) == {
        "CREATED",
        "QUEUED",
        "PREPARING",
        "INGESTING",
        "RECONNAISSANCE",
        "PARSING",
        "INDEXING",
        "GRAPH_BUILDING",
        "BASELINE_ANALYSIS",
        "SYSTEM_RECONSTRUCTION",
        "CONTRACT_DISCOVERY",
        "GAP_ANALYSIS",
        "HYPOTHESIS_ANALYSIS",
        "VERIFICATION",
        "COUNTER_ANALYSIS",
        "JUDGING",
        "REPORTING",
        "REMEDIATION",
        "REVALIDATION",
        "COMPLETED",
        "PARTIAL",
        "FAILED",
        "CANCELLED",
    }

    doc = (PHASE1 / "audit-state-machine.md").read_text(encoding="utf-8")
    for state, definition in states.items():
        assert re.search(rf"\b{re.escape(state)}\b", doc), f"{state}: missing from state-machine documentation"
        for target in definition["transitions"]:
            assert re.search(
                rf"{re.escape(state)}\s*->\s*{re.escape(target)}",
                doc,
            ), f"documented transition missing: {state} -> {target}"


def validate_required_docs() -> None:
    actual = {path.name for path in PHASE1.glob("*.md")}
    missing = REQUIRED_DOCS - actual
    assert not missing, f"missing Phase 1 documents: {sorted(missing)}"

    root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/phase-1/" in root_readme, "root README must link to Phase 1 authority"
    assert "Phase 1 — Product Definition & Technical Specification" in root_readme


def main() -> int:
    checks = [
        validate_required_docs,
        validate_json_files,
        validate_schema_inventory,
        validate_relative_refs,
        validate_state_machine,
        assert_no_stale_typo,
    ]

    for check in checks:
        check()
        print(f"PASS  {check.__name__}")

    print("Phase 1 specification validation: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, json.JSONDecodeError) as exc:
        print(f"FAIL  {exc}", file=sys.stderr)
        raise SystemExit(1)
