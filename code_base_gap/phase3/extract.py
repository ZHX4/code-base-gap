"""AST-backed semantic extraction with explicit heuristic boundaries."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .models import (
    ConfigRecord, EndpointRecord, ImportRecord, IntegrationRecord, ParsedFile,
    QueryRecord, ReferenceRecord, Span, SymbolRecord, TestRecord,
)
from .parser import ParseTree

SYMBOL_KINDS = {
    "function_definition": "function", "async_function_definition": "function",
    "class_definition": "class", "function_declaration": "function", "method_definition": "method",
    "generator_function_declaration": "function", "function_expression": "function",
}
CALL_INTEGRATIONS = {
    "fetch": "http", "axios": "http", "request": "http", "got": "http",
    "requests": "http", "httpx": "http", "urllib": "http", "boto3": "cloud",
    "redis": "cache", "ioredis": "cache", "prisma": "database", "sqlalchemy": "database",
    "psycopg": "database", "pg": "database", "mysql": "database", "mysql2": "database",
    "mongoose": "database", "mongodb": "database",
}
QUERY_TYPES = {"select_statement": "SELECT", "insert_statement": "INSERT", "update_statement": "UPDATE", "delete_statement": "DELETE", "create_table_statement": "CREATE_TABLE", "alter_table_statement": "ALTER_TABLE", "drop_table_statement": "DROP_TABLE"}
IDENTIFIER_TYPES = {"identifier", "property_identifier", "type_identifier", "shorthand_property_identifier_pattern"}


@dataclass(frozen=True)
class _Context:
    symbol_id: str | None


def _span(node: object) -> Span:
    return Span(
        start_byte=int(node.start_byte), end_byte=int(node.end_byte),
        start=type("P", (), {"line": int(node.start_point[0]) + 1, "column": int(node.start_point[1]) + 1})(),
        end=type("P", (), {"line": int(node.end_point[0]) + 1, "column": int(node.end_point[1]) + 1})(),
    )


def _text(node: object, source: bytes) -> str:
    return source[int(node.start_byte):int(node.end_byte)].decode("utf-8", errors="replace")


def _field(node: object, name: str) -> object | None:
    try:
        return node.child_by_field_name(name)
    except Exception:
        return None


def _walk(root: object):
    stack = [(root, None)]
    while stack:
        node, context = stack.pop()
        yield node, context
        children = list(getattr(node, "named_children", []))
        for child in reversed(children):
            stack.append((child, context))


def _name_node(node: object) -> object | None:
    for field in ("name", "left", "function", "identifier"):
        candidate = _field(node, field)
        if candidate is not None and getattr(candidate, "type", "") in IDENTIFIER_TYPES | {"identifier"}:
            return candidate
    for child in getattr(node, "named_children", []):
        if getattr(child, "type", "") in IDENTIFIER_TYPES:
            return child
    return None


def _extract_symbols(tree: ParseTree) -> tuple[list[SymbolRecord], dict[int, str]]:
    symbols: list[SymbolRecord] = []
    node_to_symbol: dict[int, str] = {}
    serial = 0
    for node, _ in _walk(tree.root):
        kind = SYMBOL_KINDS.get(getattr(node, "type", ""))
        if not kind:
            continue
        name_node = _name_node(node)
        if name_node is None:
            continue
        name = _text(name_node, tree.source).strip()
        if not name:
            continue
        symbol_id = f"{tree.source_sha256[:16]}:{serial}:{kind}:{name}"
        serial += 1
        parent_symbol = None
        # Parent symbol is resolved by smallest containing symbol after extraction.
        symbol = SymbolRecord(symbol_id, name, kind, _span(node), parent_symbol)
        symbols.append(symbol)
        node_to_symbol[int(node.start_byte)] = symbol_id
    symbols.sort(key=lambda s: (s.span.start_byte, -(s.span.end_byte - s.span.start_byte)))
    for index, symbol in enumerate(symbols):
        parent = None
        for candidate in symbols[:index]:
            if candidate.span.start_byte <= symbol.span.start_byte and candidate.span.end_byte >= symbol.span.end_byte and candidate.symbol_id != symbol.symbol_id:
                if parent is None or candidate.span.end_byte - candidate.span.start_byte < parent.span.end_byte - parent.span.start_byte:
                    parent = candidate
        if parent:
            symbols[index] = SymbolRecord(symbol.symbol_id, symbol.name, symbol.kind, symbol.span, parent.symbol_id, symbol.exported, symbol.signature)
    return symbols, node_to_symbol


def _extract_imports(tree: ParseTree) -> list[ImportRecord]:
    records: list[ImportRecord] = []
    patterns = [
        re.compile(r"^\s*import\s+(.+?)\s+from\s+[\"']([^\"']+)[\"']", re.M),
        re.compile(r"^\s*import\s+[\"']([^\"']+)[\"']", re.M),
        re.compile(r"^\s*from\s+([^\s]+)\s+import\s+(.+)$", re.M),
    ]
    text = tree.source.decode("utf-8", errors="replace")
    for pattern in patterns:
        for match in pattern.finditer(text):
            source = match.group(2) if match.lastindex == 2 and "from" in match.group(0) else match.group(1)
            imported_text = match.group(1) if " from " in match.group(0) else (match.group(2) if match.lastindex == 2 else "*")
            imported = tuple(x.strip() for x in re.split(r"[,{}]", imported_text) if x.strip())
            records.append(ImportRecord(source, imported, imported, "static", _span_from_text(tree.source, match.start(), match.end())))
    return _dedup(records, lambda x: (x.source, x.span.start_byte, x.span.end_byte))


def _extract_exports(tree: ParseTree, symbols: list[SymbolRecord]) -> list[SymbolRecord]:
    exported_spans = []
    text = tree.source.decode("utf-8", errors="replace")
    for match in re.finditer(r"^\s*export\s+(?:default\s+)?(?:async\s+)?(?:function|class)\s+([A-Za-z_$][\w$]*)", text, re.M):
        exported_spans.append((match.group(1), _span_from_text(tree.source, match.start(), match.end())))
    exports: list[SymbolRecord] = []
    for symbol in symbols:
        if any(name == symbol.name and span.start_byte <= symbol.span.start_byte <= span.end_byte for name, span in exported_spans):
            exports.append(SymbolRecord(symbol.symbol_id, symbol.name, symbol.kind, symbol.span, symbol.parent_symbol_id, True, symbol.signature))
    return exports


def _extract_references(tree: ParseTree, symbols: list[SymbolRecord], imports: list[ImportRecord]) -> list[ReferenceRecord]:
    definition_ranges = [(s.span.start_byte, s.span.end_byte) for s in symbols]
    import_ranges = [(i.span.start_byte, i.span.end_byte) for i in imports]
    references: list[ReferenceRecord] = []
    for node, context in _walk(tree.root):
        if getattr(node, "type", "") not in IDENTIFIER_TYPES:
            continue
        start, end = int(node.start_byte), int(node.end_byte)
        if any(a <= start and end <= b for a, b in definition_ranges + import_ranges):
            continue
        references.append(ReferenceRecord(_text(node, tree.source), "identifier", _span(node), None, None))
    return _dedup(references, lambda x: (x.name, x.span.start_byte, x.span.end_byte))


def _extract_calls(tree: ParseTree) -> tuple[list[IntegrationRecord], list[TestRecord]]:
    integrations: list[IntegrationRecord] = []
    tests: list[TestRecord] = []
    text = tree.source.decode("utf-8", errors="replace")
    for node, _ in _walk(tree.root):
        if getattr(node, "type", "") not in {"call", "call_expression", "new_expression"}:
            continue
        callee = _field(node, "function") or _field(node, "function_call") or _field(node, "method")
        call_text = _text(callee, tree.source) if callee is not None else _text(node, tree.source).split("(", 1)[0]
        base = re.split(r"[.$]", call_text.strip())[-1]
        integration_kind = CALL_INTEGRATIONS.get(base.lower())
        if integration_kind:
            integrations.append(IntegrationRecord(base, integration_kind, _span(node)))
        if base.lower() in {"test", "it", "describe", "suite", "pytest"}:
            tests.append(TestRecord("javascript" if base.lower() in {"test", "it", "describe", "suite"} else "pytest", call_text, _span(node)))
    for match in re.finditer(r"^\s*def\s+(test_[A-Za-z0-9_]+)\s*\(", text, re.M):
        tests.append(TestRecord("pytest", match.group(1), _span_from_text(tree.source, match.start(), match.end())))
    return _dedup(integrations, lambda x: (x.integration, x.span.start_byte)), _dedup(tests, lambda x: (x.name, x.span.start_byte, x.framework))


def _extract_endpoints(tree: ParseTree) -> list[EndpointRecord]:
    text = tree.source.decode("utf-8", errors="replace")
    records: list[EndpointRecord] = []
    patterns = [
        ("express", re.compile(r"\b(?:app|router)\.(get|post|put|patch|delete|options|head)\s*\(\s*['\"]([^'\"]+)['\"]", re.I)),
        ("fastapi", re.compile(r"@\w+\.(get|post|put|patch|delete|options|head)\(\s*['\"]([^'\"]+)['\"]", re.I)),
        ("flask", re.compile(r"@\w+\.route\(\s*['\"]([^'\"]+)['\"]([^\)]*)\)", re.I)),
        ("nestjs", re.compile(r"@(Get|Post|Put|Patch|Delete|Options|Head)\(\s*['\"]?([^'\")\s]*)", re.I)),
    ]
    for framework, pattern in patterns:
        for match in pattern.finditer(text):
            if framework == "flask":
                records.append(EndpointRecord(framework, None, match.group(1), _span_from_text(tree.source, match.start(), match.end())))
            else:
                records.append(EndpointRecord(framework, match.group(1).upper(), match.group(2), _span_from_text(tree.source, match.start(), match.end())))
    return _dedup(records, lambda x: (x.framework, x.method, x.path, x.span.start_byte))


def _extract_queries(tree: ParseTree) -> list[QueryRecord]:
    records: list[QueryRecord] = []
    for node, _ in _walk(tree.root):
        query_kind = QUERY_TYPES.get(getattr(node, "type", ""))
        if query_kind:
            records.append(QueryRecord(query_kind, _text(node, tree.source), _span(node)))
    if tree.language in {"javascript", "typescript", "tsx", "python"}:
        text = tree.source.decode("utf-8", errors="replace")
        for match in re.finditer(r"['\"]((?:SELECT|INSERT|UPDATE|DELETE)\b.+?)['\"]", text, re.I | re.S):
            query = match.group(1).strip()
            records.append(QueryRecord(query.split(None, 1)[0].upper(), query, _span_from_text(tree.source, match.start(), match.end())))
    return _dedup(records, lambda x: (x.query_kind, x.span.start_byte, x.span.end_byte))


def _extract_configs(tree: ParseTree) -> list[ConfigRecord]:
    records: list[ConfigRecord] = []
    for node, _ in _walk(tree.root):
        node_type = getattr(node, "type", "")
        if node_type in {"pair", "block_mapping_pair", "flow_pair", "mapping_pair"}:
            key = _field(node, "key") or _field(node, "name") or (node.named_children[0] if getattr(node, "named_children", []) else None)
            if key is not None:
                records.append(ConfigRecord(_text(key, tree.source).strip('"\''), "mapping-key", _span(node)))
    return _dedup(records, lambda x: (x.key, x.span.start_byte))


def _span_from_text(source: bytes, start: int, end: int) -> Span:
    def point(offset: int):
        prefix = source[:offset]
        line = prefix.count(b"\n") + 1
        last = prefix.rfind(b"\n")
        column = offset - (last + 1) + 1
        return type("P", (), {"line": line, "column": column})()
    from .models import Position
    return Span(start, end, Position(point(start).line, point(start).column), Position(point(end).line, point(end).column))


def _dedup(items, key):
    seen = set()
    result = []
    for item in items:
        marker = key(item)
        if marker not in seen:
            seen.add(marker)
            result.append(item)
    return result


def extract_parsed_file(tree: ParseTree, relative_path: str) -> ParsedFile:
    if tree.root is None:
        return ParsedFile(relative_path, tree.language, tree.source_sha256, len(tree.source), "", tree.has_errors, tree.error_count, (), (), (), (), (), (), (), (), (), tree.limitations)
    symbols, _ = _extract_symbols(tree)
    imports = _extract_imports(tree)
    exports = _extract_exports(tree, symbols)
    references = _extract_references(tree, symbols, imports)
    integrations, tests = _extract_calls(tree)
    endpoints = _extract_endpoints(tree)
    queries = _extract_queries(tree)
    configs = _extract_configs(tree)
    return ParsedFile(
        path=relative_path, language=tree.language, source_sha256=tree.source_sha256,
        byte_length=len(tree.source), root_type=str(tree.root.type), has_errors=tree.has_errors,
        error_count=tree.error_count, ast_nodes=tree.nodes, symbols=tuple(symbols), imports=tuple(imports),
        exports=tuple(exports), references=tuple(references), endpoints=tuple(endpoints), queries=tuple(queries),
        configs=tuple(configs), integrations=tuple(integrations), tests=tuple(tests), limitations=tree.limitations,
    )
