"""Safe Tree-sitter parsing with explicit resource bounds."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Parser
from tree_sitter_language_pack import get_language

from .models import AstNodeRecord, Position, SemanticIndexConfig, Span

LANGUAGE_BY_SUFFIX = {
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".tsx": "tsx", ".mts": "typescript", ".cts": "typescript",
    ".py": "python", ".pyi": "python", ".sql": "sql", ".json": "json", ".jsonc": "json",
    ".yaml": "yaml", ".yml": "yaml", ".dockerfile": "dockerfile",
}
SPECIAL_LANGUAGE = {"Dockerfile": "dockerfile", "Containerfile": "dockerfile"}


@dataclass(frozen=True)
class ParseTree:
    path: str
    language: str
    source: bytes
    source_sha256: str
    root: object
    nodes: tuple[AstNodeRecord, ...]
    has_errors: bool
    error_count: int
    limitations: tuple[str, ...]


def detect_language(path: Path) -> str | None:
    return SPECIAL_LANGUAGE.get(path.name) or LANGUAGE_BY_SUFFIX.get(path.suffix.lower())


def _span(node: object) -> Span:
    return Span(
        start_byte=int(node.start_byte), end_byte=int(node.end_byte),
        start=Position(int(node.start_point[0]) + 1, int(node.start_point[1]) + 1),
        end=Position(int(node.end_point[0]) + 1, int(node.end_point[1]) + 1),
    )


def _build_nodes(root: object, config: SemanticIndexConfig) -> tuple[tuple[AstNodeRecord, ...], bool, tuple[str, ...]]:
    records: list[AstNodeRecord] = []
    limitations: list[str] = []
    stack: list[tuple[object, int | None, str | None, int]] = [(root, None, None, 0)]
    next_id = 0
    truncated = False
    while stack:
        node, parent_id, field_name, depth = stack.pop()
        if len(records) >= config.max_ast_nodes_per_file:
            truncated = True
            break
        if depth > config.max_ast_depth:
            truncated = True
            continue
        node_id = next_id
        next_id += 1
        children = list(node.named_children if hasattr(node, "named_children") else [])
        records.append(AstNodeRecord(
            node_id=node_id, parent_id=parent_id, node_type=str(node.type),
            named=bool(getattr(node, "is_named", True)), span=_span(node), child_ids=(), field_name=field_name,
        ))
        for index in range(len(children) - 1, -1, -1):
            child = children[index]
            child_field = node.field_name_for_child(index) if hasattr(node, "field_name_for_child") else None
            stack.append((child, node_id, child_field, depth + 1))
    if truncated:
        limitations.append("AST traversal truncated by configured node/depth limits")
    children_by_parent: dict[int, list[int]] = {}
    for record in records:
        if record.parent_id is not None:
            children_by_parent.setdefault(record.parent_id, []).append(record.node_id)
    rebuilt = tuple(
        AstNodeRecord(
            node_id=r.node_id, parent_id=r.parent_id, node_type=r.node_type, named=r.named,
            span=r.span, child_ids=tuple(children_by_parent.get(r.node_id, [])), field_name=r.field_name,
        )
        for r in records
    )
    return rebuilt, truncated, tuple(limitations)


def parse_file(path: Path, config: SemanticIndexConfig) -> ParseTree | None:
    language_name = detect_language(path)
    if language_name is None:
        return None
    if path.is_symlink():
        return ParseTree(str(path), language_name, b"", "", None, (), False, 0, ("symlink source is not followed",))
    try:
        source = path.read_bytes()
    except OSError as exc:
        return ParseTree(str(path), language_name, b"", "", None, (), False, 0, (f"unreadable source: {type(exc).__name__}",))
    digest = hashlib.sha256(source).hexdigest()
    if len(source) > config.max_source_text_bytes or len(source) > config.max_file_bytes:
        return ParseTree(str(path), language_name, b"", digest, None, (), False, 0, ("source exceeds configured parsing byte limit",))
    try:
        language = get_language(language_name)
        parser = Parser(language)
        tree = parser.parse(source)
        nodes, truncated, limits = _build_nodes(tree.root_node, config)
        error_count = 0
        walk = [tree.root_node]
        while walk:
            node = walk.pop()
            if node.type == "ERROR" or bool(getattr(node, "is_missing", False)):
                error_count += 1
            walk.extend(list(getattr(node, "named_children", [])))
        if truncated:
            limits = (*limits, "complete AST structure is not materialized because configured traversal limits were reached")
        return ParseTree(str(path), language_name, source, digest, tree.root_node, nodes, error_count > 0, error_count, limits)
    except Exception as exc:
        return ParseTree(str(path), language_name, source, digest, None, (), False, 0, (f"parser failure: {type(exc).__name__}",))
