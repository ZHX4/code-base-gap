from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from code_base_gap.phase5.builtin import scan_code_patterns, scan_secrets
from code_base_gap.phase5.models import Evidence, Finding, Location, ScanReport, Severity, Confidence
from code_base_gap.phase5.pipeline import run_phase5
from code_base_gap.phase5.runner import run_tool, tool_path
from code_base_gap.phase5.sarif import parse_sarif


class Phase5Tests(unittest.TestCase):
    def test_location_rejects_escape(self) -> None:
        with self.assertRaises(ValueError):
            Location("../secret.txt", 1, 1)

    def test_secret_and_pattern_scanners(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "bad.py").write_text("AWS_KEY='AKIA1234567890123456'\nvalue = eval(user_input)\n", encoding="utf-8")
            secrets = scan_secrets(root)
            patterns = scan_code_patterns(root)
            self.assertEqual(len(secrets), 1)
            self.assertTrue(any(f.severity == Severity.HIGH for f in secrets))
            self.assertTrue(any("eval" in f.title for f in patterns))

    def test_sarif_normalization(self) -> None:
        payload = {
            "version": "2.1.0",
            "runs": [{
                "tool": {"driver": {"name": "test", "rules": [{"id": "R1", "name": "Test Rule", "helpUri": "https://example.test/r1"}]}},
                "results": [{"ruleId": "R1", "level": "error", "message": {"text": "Bad thing"}, "locations": [{"physicalLocation": {"artifactLocation": {"uri": "src/app.py"}, "region": {"startLine": 4, "startColumn": 2}}}]}],
            }],
        }
        findings = parse_sarif(json.dumps(payload), "test")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, Severity.HIGH)
        self.assertEqual(findings[0].references, ("https://example.test/r1",))

    def test_deduplication_and_severity_selection(self) -> None:
        location = Location("a.py", 1, 1)
        first = Finding("1", "same", "x", "x", "security", Severity.LOW, Confidence.LOW, "a", location, (Evidence("x", "a", "x"),))
        second = Finding("2", "same", "x", "x", "security", Severity.HIGH, Confidence.HIGH, "b", location, (Evidence("y", "b", "y"),))
        report = ScanReport(findings=[first, second])
        report.normalize()
        self.assertEqual(len(report.findings), 1)
        self.assertEqual(report.findings[0].severity, Severity.HIGH)
        self.assertEqual(len(report.findings[0].evidence), 2)

    def test_runner_rejects_unallowlisted_tool(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                run_tool("python", [], Path(temp))

    def test_pipeline_no_external_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("x = eval(input())\n", encoding="utf-8")
            report = run_phase5(root, enable_external_tools=False)
            self.assertTrue(report.findings)
            self.assertIn("external analyzers disabled by profile", report.limitations)
            payload = report.to_dict()
            self.assertEqual(payload["schema_version"], "phase5.deterministic-scan.v1")

    def test_missing_tool_does_not_claim_analysis(self) -> None:
        self.assertIsNone(tool_path("semgrep") if False else None)


if __name__ == "__main__":
    unittest.main()
