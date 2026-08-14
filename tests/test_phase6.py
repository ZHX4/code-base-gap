from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from code_base_gap.phase6.inputs import load_inputs
from code_base_gap.phase6.models import Provenance, SystemModel
from code_base_gap.phase6.pipeline import reconstruct_system
from code_base_gap.phase6.reconstruct import reconstruct_system as reconstruct_from_payloads


REV = "a" * 40


def _fixture() -> tuple[dict, dict]:
    phase2 = {
        "manifest": {
            "source": "local", "requested_ref": None, "repository_revision": REV, "source_kind": "local", "workspace": "/tmp/work",
            "files": [], "exclusions": [], "limitations": [], "stats": {}, "repository_metadata": {},
        },
        "reconnaissance": {
            "languages": {"python": 2}, "frameworks": ["fastapi"], "package_managers": ["pip"], "build_systems": [],
            "test_frameworks": ["pytest"], "cicd": ["github-actions"], "deployment": [], "source_roots": ["src"],
            "likely_entry_points": ["src/api.py"], "configuration_files": ["pyproject.toml"], "documentation_files": ["README.md"], "limitations": [],
        },
    }
    graph = {
        "schema_version": "phase4.program-knowledge-graph.v1", "repository_revision": REV, "limitations": [],
        "nodes": [
            {"node_id": "file:api", "kind": "file", "label": "src/api.py", "properties": {"path": "src/api.py", "language": "python"}},
            {"node_id": "endpoint:1", "kind": "endpoint", "label": "/users", "properties": {"path": "/users", "method": "GET", "handler_hint": None}},
            {"node_id": "query:1", "kind": "query", "label": "sql", "properties": {"query_kind": "sql", "text": "SELECT * FROM users"}},
            {"node_id": "ext:1", "kind": "external_module", "label": "httpx", "properties": {"module": "httpx"}},
        ],
        "edges": [
            {"edge_id": "e1", "source": "file:api", "target": "endpoint:1", "kind": "EXPOSES", "properties": {}},
            {"edge_id": "e2", "source": "file:api", "target": "query:1", "kind": "EXECUTES_QUERY", "properties": {}},
            {"edge_id": "e3", "source": "file:api", "target": "ext:1", "kind": "IMPORTS", "properties": {}},
        ],
    }
    return phase2, graph


class Phase6Tests(unittest.TestCase):
    def test_reconstructs_components_entrypoints_stores_and_dependencies(self) -> None:
        phase2, graph = _fixture()
        model = reconstruct_from_payloads(phase2, graph)
        self.assertEqual(model.repository_revision, REV)
        self.assertEqual(len(model.components), 1)
        self.assertEqual(model.components[0].name, "src")
        self.assertEqual(model.components[0].provenance, Provenance.INFERRED)
        self.assertEqual(model.components[0].frameworks, ())
        self.assertEqual(len(model.entry_points), 1)
        self.assertEqual(model.entry_points[0].provenance, Provenance.OBSERVED)
        self.assertIsNone(model.entry_points[0].symbol_id)
        self.assertEqual(len(model.data_stores), 1)
        self.assertEqual(len(model.external_dependencies), 1)
        self.assertTrue(model.trust_boundaries)
        self.assertTrue(model.critical_paths)
        valid_ids = {item.component_id for item in model.components} | {item.entry_point_id for item in model.entry_points} | {item.data_store_id for item in model.data_stores} | {item.dependency_id for item in model.external_dependencies} | {item.boundary_id for item in model.trust_boundaries}
        for path in model.critical_paths:
            self.assertTrue(set(path.steps).issubset(valid_ids))

    def test_repository_level_signals_are_preserved(self) -> None:
        phase2, graph = _fixture()
        model = reconstruct_from_payloads(phase2, graph)
        categories = {signal.category for signal in model.signals}
        self.assertTrue({"language", "framework", "package-manager", "test-framework", "cicd", "source-root"}.issubset(categories))

    def test_revision_mismatch_is_rejected(self) -> None:
        phase2, graph = _fixture()
        graph["repository_revision"] = "b" * 40
        with self.assertRaises(ValueError):
            reconstruct_from_payloads(phase2, graph)

    def test_input_loader_rejects_orphan_and_duplicate_ids(self) -> None:
        phase2, graph = _fixture()
        graph["edges"].append({"edge_id": "bad", "source": "missing", "target": "file:api", "kind": "EXPOSES", "properties": {}})
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            p2 = root / "audit.json"
            p4 = root / "graph.json"
            p2.write_text(json.dumps(phase2), encoding="utf-8")
            p4.write_text(json.dumps(graph), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_inputs(p2, p4)
        phase2, graph = _fixture()
        graph["nodes"].append(graph["nodes"][0].copy())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            p2 = root / "audit.json"
            p4 = root / "graph.json"
            p2.write_text(json.dumps(phase2), encoding="utf-8")
            p4.write_text(json.dumps(graph), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_inputs(p2, p4)

    def test_file_pipeline_is_reproducible(self) -> None:
        phase2, graph = _fixture()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            p2 = root / "audit.json"
            p4 = root / "graph.json"
            p2.write_text(json.dumps(phase2), encoding="utf-8")
            p4.write_text(json.dumps(graph), encoding="utf-8")
            first = reconstruct_system(p2, p4).to_dict()
            second = reconstruct_system(p2, p4).to_dict()
            self.assertEqual(first, second)

    def test_empty_model_is_valid(self) -> None:
        model = SystemModel()
        model.normalize()
        self.assertEqual(model.stats["components"], 0)


if __name__ == "__main__":
    unittest.main()
