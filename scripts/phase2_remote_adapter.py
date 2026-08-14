"""Compatibility wrapper for the Phase 2 GitHub source adapter."""
from __future__ import annotations

from dataclasses import dataclass

from code_base_gap.phase2.source import SourceError, parse_github_source


@dataclass(frozen=True)
class RemoteRevision:
    source: str
    requested_ref: str
    revision: str


class RemoteRepositoryError(RuntimeError):
    pass


def validate_source(source: str) -> tuple[str, str]:
    try:
        return parse_github_source(source)
    except SourceError as exc:
        raise RemoteRepositoryError(str(exc)) from exc
