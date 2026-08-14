from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from code_base_gap.phase2.filesystem import inventory
from code_base_gap.phase2.models import AuditInput
from code_base_gap.phase2.pipeline import run_phase2
from code_base_gap.phase2.source import SourceError, parse_github_source


class Phase2Tests(unittest.TestCase):
    def test_github_source_parser(self) -> None:
        self.assertEqual(parse_github_source("https://github.com/example/project.git"), ("example", "project"))
        with self.assertRaises(SourceError):
            parse_github_source("https://gitlab.com/example/project")
        with self.assertRaises(SourceError):
            parse_github_source("https://github.com/example/project/issues/1")

    def test_inventory_classification_and_exclusions(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "node_modules").mkdir()
            (root / "src" / "main.ts").write_text("export const ok = true\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "main.test.ts").write_text("test('ok', () => {})\n", encoding="utf-8")
            (root / "package.json").write_text('{"dependencies":{"next":"1.0.0"}}', encoding="utf-8")
            files, exclusions, limitations = inventory(root, 100, 1_000_000, 10_000_000)
            self.assertFalse(limitations)
            self.assertIn("node_modules", exclusions)
            by_path = {entry.path: entry for entry in files}
            self.assertEqual(by_path["src/main.ts"].language, "TypeScript")
            self.assertTrue(by_path["tests/main.test.ts"].is_test)
            self.assertTrue(by_path["package.json"].is_config)

    def test_limits_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index in range(5):
                (root / f"file{index}.txt").write_text("x", encoding="utf-8")
            files, _, limitations = inventory(root, 3, 100, 100)
            self.assertEqual(len(files), 3)
            self.assertTrue(any(item.startswith("file_count_limit:") for item in limitations))

    def test_phase2_local_pipeline_is_non_executing_and_machine_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "package.json").write_text(
                json.dumps({"dependencies": {"express": "1.0.0"}, "scripts": {"test": "echo should-not-run"}}),
                encoding="utf-8",
            )
            (root / "server.js").write_text("module.exports = {};\n", encoding="utf-8")
            result = run_phase2(AuditInput(str(root)))
            self.assertEqual(result.manifest.source_kind, "local")
            self.assertEqual(result.manifest.repository_revision, "unversioned")
            self.assertIn("JavaScript", result.reconnaissance.languages)
            self.assertIn("Express", result.reconnaissance.frameworks)
            self.assertIn("package.json test scripts", result.reconnaissance.test_frameworks)
            policy = result.manifest.repository_metadata["execution_policy"]
            self.assertTrue(all(value is False for value in policy.values()))

    def test_invalid_limits_fail(self) -> None:
        with self.assertRaises(ValueError):
            run_phase2(AuditInput(".", max_files=0))


if __name__ == "__main__":
    unittest.main()
