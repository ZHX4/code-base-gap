"""Deterministic finding fingerprints."""
from __future__ import annotations

import hashlib


def finding_fingerprint(tool: str, rule: str, path: str | None, line: int | None, title: str) -> str:
    material = "\x1f".join(str(x or "") for x in (tool, rule, path, line, title)).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def finding_id(fingerprint: str) -> str:
    return f"finding:{fingerprint[:24]}"
