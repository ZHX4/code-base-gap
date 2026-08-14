"""Conservative cross-file resolution for imports and identifier references."""
from __future__ import annotations

import posixpath
from pathlib import PurePosixPath
from typing import Iterable

from code_base_gap.phase3.models import ImportRecord, ParsedFile, ReferenceRecord, SymbolRecord


JS_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx", ".mts", ".cts", ".mjs", ".cjs")
PY_EXTENSIONS = (".py",)


def _strip_known_extension(path: str) -> str:
    for suffix in (*JS_EXTENSIONS, *PY_EXTENSIONS):
        if path.endswith(suffix):
            return path[: -len(suffix)]
    return path


def _python_relative_base(source_path: str, module: str) -> str:
    source_dir = PurePosixPath(source_path).parent
    dots = len(module) - len(module.lstrip("."))
    remainder = module[dots:]
    parent = source_dir
    for _ in range(max(0, dots - 1)):
        parent = parent.parent
    return posixpath.normpath((parent / remainder.replace(".", "/")).as_posix())


def _candidate_paths(source_path: str, module: str) -> list[str]:
    if source_path.endswith(".py") and module.startswith("."):
        base = _python_relative_base(source_path, module)
    elif module.startswith("."):
        source_dir = PurePosixPath(source_path).parent
        base = posixpath.normpath((source_dir / module).as_posix())
    else:
        base = module.replace(".", "/")
    base = _strip_known_extension(base)
    candidates = [base]
    for ext in JS_EXTENSIONS:
        candidates.append(base + ext)
    for ext in PY_EXTENSIONS:
        candidates.append(base + ext)
    candidates.extend([
        base.rstrip("/") + "/index.ts",
        base.rstrip("/") + "/index.tsx",
        base.rstrip("/") + "/index.js",
        base.rstrip("/") + "/__init__.py",
    ])
    normalized = []
    for path in candidates:
        value = posixpath.normpath(path).lstrip("./")
        if value != ".." and not value.startswith("../"):
            normalized.append(value)
    return list(dict.fromkeys(normalized))


def resolve_import(source_path: str, record: ImportRecord, files: set[str]) -> str | None:
    candidates = _candidate_paths(source_path, record.source)
    matches = [candidate for candidate in candidates if candidate in files]
    return matches[0] if len(matches) == 1 else None


def unique_symbols_by_name(files: Iterable[ParsedFile]) -> dict[str, list[tuple[str, SymbolRecord]]]:
    result: dict[str, list[tuple[str, SymbolRecord]]] = {}
    for parsed_file in files:
        for symbol in parsed_file.symbols:
            result.setdefault(symbol.name, []).append((parsed_file.path, symbol))
    return result


def resolve_reference(
    parsed_file: ParsedFile,
    reference: ReferenceRecord,
    local_symbols: list[SymbolRecord],
    global_by_name: dict[str, list[tuple[str, SymbolRecord]]],
) -> tuple[str, SymbolRecord] | None:
    local = [symbol for symbol in local_symbols if symbol.name == reference.name]
    containing = [
        symbol for symbol in local
        if symbol.span.start_byte <= reference.span.start_byte
        and symbol.span.end_byte >= reference.span.end_byte
    ]
    if len(containing) == 1:
        return parsed_file.path, containing[0]

    same_file = [symbol for symbol in local if symbol.span.start_byte <= reference.span.start_byte]
    if len(same_file) == 1:
        return parsed_file.path, same_file[0]

    global_matches = global_by_name.get(reference.name, [])
    return global_matches[0] if len(global_matches) == 1 else None
