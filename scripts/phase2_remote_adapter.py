"""Phase 2 remote adapter boundary.

The implementation keeps network acquisition behind one interface so later
production workers can enforce centralized egress policy without changing
reconnaissance logic.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RemoteRevision:
    source: str
    requested_ref: str
    revision: str


class RemoteRepositoryError(RuntimeError):
    pass


def validate_source(source: str) -> None:
    if not source.startswith("https://github.com/"):
        raise RemoteRepositoryError("Phase 2 currently accepts public HTTPS GitHub sources only")
