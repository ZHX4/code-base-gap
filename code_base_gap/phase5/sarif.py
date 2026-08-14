"""Normalize SARIF 2.1.0 results from external static-analysis tools."""
from __future__ import annotations

import json
from typing import Any

from .fingerprint import finding_fingerprint, finding_id
from .models import Confidence, Evidence, Finding, Location, Severity


def _severity(value: Any) -> Severity:
    text = str(value or "").lower()
    if text in {"error", "critical"}: return Severity.CRITICAL if text == "critical" else Severity.HIGH
    if text in {"warning", "high"}: return Severity.HIGH
    if text in {"note", "medium"}: return Severity.MEDIUM
    if text in {"low", "recommendation", "information"}: return Severity.LOW
    return Severity.UNKNOWN


def parse_sarif(text: str, tool_name: str) -> list[Finding]:
    document = json.loads(text)
    results: list[Finding] = []
    for run in document.get("runs", []):
        driver = run.get("tool", {}).get("driver", {})
        rules = {r.get("id"): r for r in driver.get("rules", []) if r.get("id")}
        for result in run.get("results", []):
            rule_id = str(result.get("ruleId") or result.get("ruleIndex") or "unknown")
            rule = rules.get(rule_id, {})
            message = result.get("message", {}).get("text") or rule.get("shortDescription", {}).get("text") or "analysis result"
            level = result.get("level") or rule.get("defaultConfiguration", {}).get("level")
            locations = result.get("locations") or [{}]
            physical = locations[0].get("physicalLocation", {})
            artifact = physical.get("artifactLocation", {})
            uri = artifact.get("uri")
            region = physical.get("region", {})
            location = Location(
                str(uri),
                region.get("startLine"), region.get("startColumn"),
                region.get("endLine"), region.get("endColumn"),
            ) if uri else None
            fp = finding_fingerprint(tool_name, rule_id, uri, region.get("startLine"), message)
            confidence_text = "high" if result.get("provenance") or result.get("fingerprints") else "medium"
            try: confidence = Confidence(confidence_text)
            except ValueError: confidence = Confidence.UNKNOWN
            evidence = Evidence("tool-result", tool_name, message, location, fp, {"rule_id": rule_id})
            cwes = tuple(str(x) for x in rule.get("properties", {}).get("cwe", []) if x)
            results.append(Finding(
                finding_id=finding_id(fp), fingerprint=fp, title=str(rule.get("name") or rule_id),
                description=message, category=str(rule.get("properties", {}).get("category", "static-analysis")),
                severity=_severity(level), confidence=confidence, source_tool=tool_name,
                location=location, evidence=(evidence,), cwe=cwes,
                references=tuple(str(x) for x in rule.get("helpUri", []) if x),
                fix_hint=rule.get("help", {}).get("text") if isinstance(rule.get("help"), dict) else None,
                metadata={"rule_id": rule_id, "sarif_rule": rule},
            ))
    return results
