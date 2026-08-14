from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from code_base_gap.phase3.models import SemanticIndexConfig
from code_base_gap.phase3.parser import detect_language, parse_file
from code_base_gap.phase3.pipeline import run_phase3


class Phase3Tests(unittest.TestCase):
    def test_language_detection(self) -> None:
        self.assertEqual(detect_language(Path("main.py")), "python")
        self.assertEqual(detect_language(Path("server.ts")), "typescript")
        self.assertEqual(detect_language(Path("component.tsx")), "tsx")
        self.assertEqual(detect_language(Path("query.sql")), "sql")
        self.assertEqual(detect_language(Path("Dockerfile")), "dockerfile")
        self.assertIsNone(detect_language(Path("README.md")))

    def test_python_symbols_imports_references_tests(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "main.py").write_text(
                "from fastapi import FastAPI\n"
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
            self.assertTrue(any(item.source == "fastapi" for item in parsed.imports))
            self.assertTrue(any(endpoint.path == "/users/{user_id}" for endpoint in parsed.endpoints))
            self.assertTrue(any(test.name == "test_get_user" for test in parsed.tests))
            self.assertGreater(len(parsed.ast_nodes), 0)
            body_reference = next((ref for ref in parsed.references if ref.name == "user_id" and ref.span.start_byte > get_user.name_span.end_byte), None)
            self.assertIsNotNone(body_reference)
            self.assertEqual(body_reference.context_symbol_id, get_user.symbol_id)

    def test_typescript_exports_http_and_sql(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "server.ts").write_text(
                "import express from 'express';\n"
                "const app = express();\n"
                "export function listUsers() { return fetch('/users'); }\n"
                "app.get('/users', listUsers);\n"
                "const sql = \"SELECT id FROM users WHERE active = 1\";\n",
                encoding="utf-8",
            )
            index = run_phase3(root)
            parsed = index.files[0]
            self.assertEqual(parsed.language, "typescript")
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

    def test_traversal_bounds_are_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "deep.py"
            path.write_text("def f():\n    return (((((((((1)))))))))\n", encoding="utf-8")
            tree = parse_file(path, SemanticIndexConfig(max_ast_nodes_per_file=5, max_ast_depth=3))
            self.assertIsNotNone(tree)
            assert tree is not None
            self.assertLessEqual(len(tree.nodes), 5)
            self.assertIn("AST traversal truncated by configured node/depth limits", tree.limitations)

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
            index = run_phase3(root, config=SemanticIndexConfig(max_files=10, max_file_bytes=1024, max_total_bytes=2048))
            self.assertEqual(len(index.files), 1)
            self.assertIn("symlink source is not followed", index.files[0].limitations)
            outside.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
