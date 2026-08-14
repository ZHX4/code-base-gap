"""Normalize SARIF 2.1.0 results from external static-analysis tools."""
from __future__ import annotations

import json
from typing import Any

from .fingerprint import finding_fingerprint, finding_id
from .models import Confidence, Evidence, Finding, Location, Severity


def _severity(value: Any) -> Severity:
    text = str(value or "").lower()
    if text == "critical": return Severity.CRITICAL
    if text in {"error", "high"}: return Severity.HIGH
    if text in {"warning", "medium"}: return Severity.MEDIUM
    if text in {"note", "low", "recommendation", "information"}: return Severity.LOW
    return Severity.UNKNOWN


def _safe_location(uri: str | None, region: dict[str, Any]) -> Location | None:
    if not uri:
        return None
    normalized = str(uri).replace("\\", "/").lstrip("./")
    try:
        return Location(normalized, region.get("startLine"), region.get("startColumn"), region.get("endLine"), region.get("endColumn"))
    except ValueError:
        return None


def parse_sarif(text: str, tool_name: str) -> list[Finding]:
    document = json.loads(text)
    results: list[Finding] = []
    for run in document.get("runs", []):
        driver = run.get("tool", {}).get("driver", {})
        rules = {str(r.get("id")): r for r in driver.get("rules", []) if r.get("id") is not None}
        for result in run.get("results", []):
            rule_id = str(result.get("ruleId") or result.get("ruleIndex") or "unknown")
            rule = rules.get(rule_id, {})
            message = result.get("message", {}).get("text") or rule.get("shortDescription", {}).get("text") or "analysis result"
            level = result.get("level") or rule.get("defaultConfiguration", {}).get("level")
            physical = ((result.get("locations") or [{}])[0]).get("physicalLocation", {})
            uri = physical.get("artifactLocation", {}).get("uri")
            region = physical.get("region", {})
            location = _safe_location(uri, region)
            fp = finding_fingerprint(tool_name, rule_id, uri, region.get("startLine"), message)
            confidence = Confidence.HIGH if result.get("fingerprints") else Confidence.MEDIUM
            help_uri = rule.get("helpUri")
            references = (str(help_uri),) if help_uri else ()
            help_obj = rule.get("help") if isinstance(rule.get("help"), dict) else {}
            evidence = Evidence("tool-result", tool_name, message, location, fp, {"rule_id": rule_id})
            results.append(Finding(
                finding_id=finding_id(fp), fingerprint=fp, title=str(rule.get("name") or rule_id),
                description=message, category=str(rule.get("properties", {}).get("category", "static-analysis")),
                severity=_severity(level), confidence=confidence, source_tool=tool_name,
                location=location, evidence=(evidence,),
                cwe=tuple(str(x) for x in rule.get("properties", {}).get("cwe", []) if x),
                references=references, fix_hint=help_obj.get("text"), metadata={"rule_id": rule_id},
            ))
    return results
