"""Repository-wide semantic indexing built on Phase 2 inventory semantics."""
from __future__ import annotations

from pathlib import Path

from .extract import extract_parsed_file
from .models import AuditManifest, ParsedFile, SemanticIndex, SemanticIndexConfig
from .parser import parse_file

SUPPORTED_KINDS = {"source", "config"}


def _resolve_entry(root: Path, relative_path: str) -> Path | None:
    candidate = root / relative_path
    try:
        resolved = candidate.resolve()
        root_resolved = root.resolve()
    except OSError:
        return None
    if resolved != root_resolved and root_resolved not in resolved.parents:
        return None
    return candidate


def build_semantic_index(
    root: Path,
    config: SemanticIndexConfig | None = None,
    manifest: AuditManifest | None = None,
    repository_revision: str | None = None,
) -> SemanticIndex:
    config = config or SemanticIndexConfig()
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"repository root is not a directory: {root}")

    index = SemanticIndex(repository_revision=repository_revision)
    if manifest is not None:
        index.repository_revision = manifest.repository_revision
        entries = [entry for entry in manifest.files if entry.kind in SUPPORTED_KINDS]
    else:
        from code_base_gap.phase2.filesystem import inventory
        entries, _, limitations = inventory(
            root,
            max_files=config.max_files,
            max_file_bytes=config.max_file_bytes,
            max_total_bytes=config.max_total_bytes,
        )
        index.limitations.extend(limitations)

    for entry in entries:
        candidate = root / entry.path
        if entry.is_symlink:
            parsed = parse_file(candidate, config)
            if parsed is None:
                continue
        else:
            path = _resolve_entry(root, entry.path)
            if path is None:
                index.limitations.append(f"skipped path outside repository root: {entry.path}")
                continue
            parsed = parse_file(path, config)
            if parsed is None:
                continue
        parsed_file: ParsedFile = extract_parsed_file(parsed, entry.path)
        index.files.append(parsed_file)
        index.limitations.extend(f"{entry.path}: {item}" for item in parsed_file.limitations)

    index.parser_versions["tree-sitter"] = "0.26.x"
    index.parser_versions["tree-sitter-language-pack"] = "1.13.3"
    index.files.sort(key=lambda item: item.path)
    index.limitations = sorted(set(index.limitations))
    index.finalize()
    return index
