"""Phase 2 orchestration: resolve, inventory, and reconnaissance."""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from .filesystem import inventory
from .models import AuditInput, AuditManifest, Phase2Result
from .recon import reconnaissance
from .source import ResolvedSource, SourceError, resolve_source


def _config_hash(config: AuditInput) -> str:
    payload = json.dumps(config.__dict__, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _stats(files) -> dict[str, int]:
    return {
        "file_count": len(files),
        "total_bytes": sum(item.size_bytes for item in files),
        "source_files": sum(item.kind == "source" for item in files),
        "config_files": sum(item.is_config for item in files),
        "documentation_files": sum(item.is_documentation for item in files),
        "test_files": sum(item.is_test for item in files),
        "generated_files": sum(item.is_generated for item in files),
        "symlinks": sum(item.is_symlink for item in files),
    }


def _workspace_metadata(resolved: ResolvedSource, config: AuditInput) -> dict[str, object]:
    return {
        "configuration_hash": _config_hash(config),
        "source_kind": resolved.source_kind,
        "requested_ref": resolved.requested_ref,
        "repository_revision": resolved.revision,
        "execution_policy": {
            "build_executed": False,
            "tests_executed": False,
            "package_install_executed": False,
            "repository_hooks_executed": False,
            "containers_started": False,
        },
    }


def run_phase2(config: AuditInput) -> Phase2Result:
    if config.max_files <= 0 or config.max_file_bytes <= 0 or config.max_total_bytes <= 0 or config.max_archive_bytes <= 0:
        raise ValueError("all Phase 2 limits must be positive")

    resolved, holder = resolve_source(config.source, config.ref, config.max_archive_bytes)
    try:
        files, exclusions, limitations = inventory(
            resolved.workspace,
            max_files=config.max_files,
            max_file_bytes=config.max_file_bytes,
            max_total_bytes=config.max_total_bytes,
        )
        manifest = AuditManifest(
            source=resolved.source,
            requested_ref=resolved.requested_ref,
            repository_revision=resolved.revision,
            source_kind=resolved.source_kind,
            workspace=str(resolved.workspace),
            files=files,
            exclusions=exclusions,
            limitations=limitations,
            stats=_stats(files),
            repository_metadata=_workspace_metadata(resolved, config) | resolved.repository_metadata,
        )
        report = reconnaissance(resolved.workspace, manifest)
        return Phase2Result(manifest=manifest, reconnaissance=report)
    finally:
        if holder is not None:
            holder.cleanup()


def write_result(result: Phase2Result, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
