"""Stable identifiers for graph entities and relationships."""
from __future__ import annotations

import hashlib


def stable_id(kind: str, *parts: object) -> str:
    material = "\x1f".join(str(part) for part in (kind, *parts))
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
    return f"{kind}:{digest}"


def edge_id(kind: str, source: str, target: str, *parts: object) -> str:
    return stable_id("edge", kind, source, target, *parts)
