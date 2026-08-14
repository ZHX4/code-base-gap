from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from code_base_gap.phase5.builtin import scan_code_patterns, scan_secrets
from code_base_gap.phase5.models import Confidence, Evidence, Finding, Location, ScanReport, Severity, ToolMetadata, ToolRun
from code_base_gap.phase5.pipeline import run_phase5
from code_base_gap.phase5.runner import run_tool
from code_base_gap.phase5.sarif import parse_sarif


class Phase5Tests(unittest.TestCase):
    def test_location_rejects_escape_and_uri_paths(self) -> None:
        for value in ("../secret.txt", "/etc/passwd", r"C:\\secret.txt", "C:secret.txt", "file:///tmp/x", "https://example.com/x"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    Location(value, 1, 1)

    def test_secret_and_pattern_scanners(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "bad.py").write_text("AWS_KEY='AKIA1234567890123456'\nvalue = eval(user_input)\n", encoding="utf-8")
            secrets = scan_secrets(root)
            patterns = scan_code_patterns(root)
            self.assertEqual(len(secrets), 1)
            self.assertTrue(any(f.severity == Severity.HIGH for f in secrets))
            self.assertEqual(sum("Dynamic code evaluation" in f.title for f in patterns), 1)

    def test_excluded_dependency_directory_is_not_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dep = root / "node_modules" / "pkg"
            dep.mkdir(parents=True)
            (dep / "bad.py").write_text("eval(input())\n", encoding="utf-8")
            self.assertEqual(scan_code_patterns(root), [])

    def test_scanner_limits_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a.py").write_text("eval(x)\n", encoding="utf-8")
            (root / "b.py").write_text("eval(x)\n", encoding="utf-8")
            self.assertEqual(len(scan_code_patterns(root, max_files=1)), 1)
            self.assertEqual(scan_code_patterns(root, max_file_bytes=1), [])

    def test_sarif_normalization(self) -> None:
        payload = {
            "version": "2.1.0",
            "runs": [{"tool": {"driver": {"name": "test", "rules": [{"id": "R1", "name": "Test Rule", "helpUri": "https://example.test/r1"}]}},
                "results": [{"ruleId": "R1", "level": "error", "message": {"text": "Bad thing"}, "locations": [{"physicalLocation": {"artifactLocation": {"uri": "src/app.py"}, "region": {"startLine": 4, "startColumn": 2}}}]}]}],
        }
        findings = parse_sarif(json.dumps(payload), "test")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, Severity.HIGH)
        self.assertEqual(findings[0].references, ("https://example.test/r1",))
        self.assertEqual(findings[0].location.path, "src/app.py")

    def test_sarif_rejects_malformed_or_external_location(self) -> None:
        with self.assertRaises(json.JSONDecodeError):
            parse_sarif("not json", "test")
        for uri in ("file:///tmp/x", "/etc/passwd", "C:/Windows/win.ini", "C:Windows/win.ini"):
            payload = {"version": "2.1.0", "runs": [{"tool": {"driver": {"rules": [{"id": "R1"}]}}, "results": [{"ruleId": "R1", "message": {"text": "x"}, "locations": [{"physicalLocation": {"artifactLocation": {"uri": uri}}}]}]}]}
            with self.subTest(uri=uri):
                finding = parse_sarif(json.dumps(payload), "test")[0]
                self.assertIsNone(finding.location)

    def test_deduplication_and_severity_selection(self) -> None:
        location = Location("a.py", 1, 1)
        first = Finding("1", "same", "x", "x", "security", Severity.HIGH, Confidence.LOW, "a", location, (Evidence("x", "a", "x"),))
        second = Finding("2", "same", "x", "x", "security", Severity.HIGH, Confidence.HIGH, "b", location, (Evidence("y", "b", "y"),))
        report = ScanReport(findings=[first, second])
        report.normalize()
        self.assertEqual(len(report.findings), 1)
        self.assertEqual(report.findings[0].confidence, Confidence.HIGH)
        self.assertEqual(len(report.findings[0].evidence), 2)

    def test_runner_rejects_unallowlisted_tool(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                run_tool("python", [], Path(temp))

    def test_pipeline_no_external_tools_and_report_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("x = eval(input())\n", encoding="utf-8")
            report = run_phase5(root, enable_external_tools=False)
            self.assertTrue(report.findings)
            self.assertIn("external analyzers disabled by profile", report.limitations)
            payload = report.to_dict()
            self.assertEqual(payload["schema_version"], "phase5.deterministic-scan.v1")
            self.assertIn("artifacts", payload)

    def test_report_redacts_tool_output(self) -> None:
        run = ToolRun(ToolMetadata("semgrep", "x", "v1", "ready"), 0, 1, False, "SECRET_OUTPUT", "SECRET_ERROR")
        report = ScanReport(tool_runs=[run])
        encoded = json.dumps(report.to_dict())
        self.assertNotIn("SECRET_OUTPUT", encoded)
        self.assertNotIn("SECRET_ERROR", encoded)


if __name__ == "__main__":
    unittest.main()
