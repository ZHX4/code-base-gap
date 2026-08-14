from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from code_base_gap.phase2.models import AuditManifest, FileEntry
from code_base_gap.phase3.models import SemanticIndexConfig
from code_base_gap.phase3.parser import detect_language
from code_base_gap.phase3.pipeline import run_phase3


class Phase3Tests(unittest.TestCase):
    def test_language_detection(self) -> None:
        self.assertEqual(detect_language(Path("main.py")), "python")
        self.assertEqual(detect_language(Path("server.ts")), "typescript")
        self.assertEqual(detect_language(Path("component.tsx")), "tsx")
        self.assertEqual(detect_language(Path("query.sql")), "sql")
        self.assertEqual(detect_language(Path("Dockerfile")), "dockerfile")
        self.assertIsNone(detect_language(Path("README.md")))

    def test_invalid_resource_limits_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SemanticIndexConfig(max_files=0)
        with self.assertRaises(ValueError):
            SemanticIndexConfig(max_ast_depth=-1)
        with self.assertRaises(ValueError):
            SemanticIndexConfig(max_file_bytes=2_000_000, max_source_text_bytes=1_000_000)

    def test_python_symbols_imports_references_tests(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "main.py").write_text(
                "from fastapi import FastAPI, APIRouter as Router\n"
                "app = FastAPI()\n"
                "@app.get('/users/{user_id}')\n"
                "def get_user(user_id):\n"
                "    return user_id\n"
                "def test_get_user():\n"
                "    return get_user(1)\n",
                encoding="utf-8",
            )
            index = run_phase3(root)
            parsed = index.files[0]
            self.assertEqual(parsed.language, "python")
            self.assertFalse(parsed.has_errors)
            get_user = next(symbol for symbol in parsed.symbols if symbol.name == "get_user")
            fastapi_import = next(item for item in parsed.imports if item.source == "fastapi")
            self.assertIn("APIRouter", fastapi_import.imported)
            self.assertIn("Router", fastapi_import.local_names)
            self.assertTrue(any(reference.name == "user_id" and reference.context_symbol_id == get_user.symbol_id for reference in parsed.references))
            self.assertTrue(any(reference.name == "get_user" for reference in parsed.references))
            self.assertTrue(any(endpoint.path == "/users/{user_id}" for endpoint in parsed.endpoints))
            self.assertTrue(any(test.name == "test_get_user" for test in parsed.tests))
            self.assertGreater(len(parsed.ast_nodes), 0)

    def test_non_python_files_do_not_get_python_import_heuristics(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "script.js").write_text(
                "import express from 'express';\nconst app = express();\n",
                encoding="utf-8",
            )
            index = run_phase3(root)
            parsed = index.files[0]
            self.assertEqual(parsed.language, "javascript")
            self.assertEqual(len(parsed.imports), 1)
            self.assertEqual(parsed.imports[0].source, "express")
            self.assertEqual(parsed.imports[0].kind, "static")
            self.assertEqual(parsed.imports[0].imported, ("express",))
            self.assertEqual(parsed.imports[0].local_names, ("express",))

    def test_typescript_exports_http_and_sql(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "server.ts").write_text(
                "import express, { Router as ExpressRouter } from 'express';\n"
                "const app = express();\n"
                "export function listUsers() { return fetch('/users'); }\n"
                "app.get('/users', listUsers);\n"
                "const sql = \"SELECT id FROM users WHERE active = 1\";\n",
                encoding="utf-8",
            )
            index = run_phase3(root)
            parsed = index.files[0]
            self.assertEqual(parsed.language, "typescript")
            express_import = next(item for item in parsed.imports if item.source == "express")
            self.assertIn("Router", express_import.imported)
            self.assertIn("ExpressRouter", express_import.local_names)
            self.assertTrue(any(symbol.name == "listUsers" for symbol in parsed.symbols))
            self.assertTrue(any(symbol.name == "listUsers" for symbol in parsed.exports))
            self.assertTrue(any(endpoint.path == "/users" and endpoint.method == "GET" for endpoint in parsed.endpoints))
            self.assertTrue(any(query.query_kind == "SELECT" for query in parsed.queries))
            self.assertTrue(any(integration.integration == "fetch" for integration in parsed.integrations))

    def test_sql_ast_query_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "schema.sql").write_text(
                "CREATE TABLE users (id INTEGER PRIMARY KEY);\n"
                "SELECT id FROM users;\n",
                encoding="utf-8",
            )
            index = run_phase3(root)
            parsed = index.files[0]
            self.assertEqual(parsed.language, "sql")
            self.assertTrue(any(q.query_kind == "SELECT" for q in parsed.queries))
            self.assertTrue(any(q.query_kind == "CREATE_TABLE" for q in parsed.queries))

    def test_invalid_syntax_is_retained_with_error_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "broken.py").write_text("def broken(:\n", encoding="utf-8")
            index = run_phase3(root)
            parsed = index.files[0]
            self.assertTrue(parsed.has_errors)
            self.assertGreater(parsed.error_count, 0)

    def test_ast_traversal_limit_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "main.py").write_text("\n".join(f"x{i} = {i}" for i in range(100)), encoding="utf-8")
            index = run_phase3(root, config=SemanticIndexConfig(max_ast_nodes_per_file=10, max_ast_depth=10, max_file_bytes=10_000, max_source_text_bytes=10_000, max_total_bytes=20_000))
            parsed = index.files[0]
            self.assertLessEqual(len(parsed.ast_nodes), 10)
            self.assertTrue(any("truncated" in limitation for limitation in parsed.limitations))

    def test_manifest_revision_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = AuditManifest("local", None, "abc", "local", str(root), [
                FileEntry("main.py", 0, ".py", "python", "source", False, False, False, False, False)
            ])
            with self.assertRaises(ValueError):
                from code_base_gap.phase3.indexer import build_semantic_index
                build_semantic_index(root, manifest=manifest, repository_revision="def")

    def test_limits_and_symlink_safety(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            outside = Path(temp).parent / "phase3-outside.py"
            outside.write_text("def outside(): return 1\n", encoding="utf-8")
            link = root / "linked.py"
            try:
                link.symlink_to(outside)
            except OSError:
                outside.unlink(missing_ok=True)
                self.skipTest("symlinks are unavailable on this platform")
            index = run_phase3(root, config=SemanticIndexConfig(max_files=10, max_file_bytes=1024, max_total_bytes=2048, max_source_text_bytes=1024))
            self.assertEqual(len(index.files), 1)
            self.assertIn("symlink source is not followed", index.files[0].limitations)
            outside.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
