"""AST-backed semantic extraction with explicit heuristic boundaries."""
from __future__ import annotations

import re

from .models import (
    ConfigRecord, EndpointRecord, ImportRecord, IntegrationRecord, ParsedFile,
    Position, QueryRecord, ReferenceRecord, Span, SymbolRecord, TestRecord,
)
from .parser import ParseTree

SYMBOL_KINDS = {
    "function_definition": "function", "async_function_definition": "function",
    "class_definition": "class", "function_declaration": "function", "method_definition": "method",
    "generator_function_declaration": "function", "function_expression": "function",
}
CALL_INTEGRATIONS = {
    "fetch": "http", "axios": "http", "request": "http", "got": "http", "requests": "http",
    "httpx": "http", "urllib": "http", "boto3": "cloud", "redis": "cache", "ioredis": "cache",
    "prisma": "database", "sqlalchemy": "database", "psycopg": "database", "pg": "database",
    "mysql": "database", "mysql2": "database", "mongoose": "database", "mongodb": "database",
}
QUERY_TYPES = {
    "select_statement": "SELECT", "insert_statement": "INSERT", "update_statement": "UPDATE",
    "delete_statement": "DELETE", "create_table_statement": "CREATE_TABLE",
    "alter_table_statement": "ALTER_TABLE", "drop_table_statement": "DROP_TABLE",
}
IDENTIFIER_TYPES = {"identifier", "property_identifier", "type_identifier", "shorthand_property_identifier_pattern"}
JS_TS_LANGUAGES = {"javascript", "typescript", "tsx"}
PYTHON_LANGUAGES = {"python"}


def _span(node: object) -> Span:
    return Span(
        start_byte=int(node.start_byte), end_byte=int(node.end_byte),
        start=Position(int(node.start_point[0]) + 1, int(node.start_point[1]) + 1),
        end=Position(int(node.end_point[0]) + 1, int(node.end_point[1]) + 1),
    )


def _text(node: object, source: bytes) -> str:
    return source[int(node.start_byte):int(node.end_byte)].decode("utf-8", errors="replace")


def _field(node: object, name: str) -> object | None:
    try:
        return node.child_by_field_name(name)
    except Exception:
        return None


def _walk(tree: ParseTree):
    """Yield nodes within the parser's explicit traversal bounds."""
    if tree.root is None:
        return
    stack: list[tuple[object, int]] = [(tree.root, 0)]
    visited = 0
    while stack and visited < tree.max_traversal_nodes:
        node, depth = stack.pop()
        if depth > tree.max_traversal_depth:
            continue
        visited += 1
        yield node
        children = list(getattr(node, "named_children", []))
        for child in reversed(children):
            if depth + 1 <= tree.max_traversal_depth:
                stack.append((child, depth + 1))


def _name_node(node: object) -> object | None:
    for field in ("name", "left", "function", "identifier"):
        candidate = _field(node, field)
        if candidate is not None and getattr(candidate, "type", "") in IDENTIFIER_TYPES:
            return candidate
    for child in getattr(node, "named_children", []):
        if getattr(child, "type", "") in IDENTIFIER_TYPES:
            return child
    return None


def _extract_symbols(tree: ParseTree) -> list[SymbolRecord]:
    symbols: list[SymbolRecord] = []
    serial = 0
    for node in _walk(tree):
        kind = SYMBOL_KINDS.get(getattr(node, "type", ""))
        if not kind:
            continue
        name_node = _name_node(node)
        if name_node is None:
            continue
        name = _text(name_node, tree.source).strip()
        if not name:
            continue
        symbols.append(SymbolRecord(
            f"{tree.source_sha256[:16]}:{serial}:{kind}:{name}", name, kind, _span(node), _span(name_node)
        ))
        serial += 1
    symbols.sort(key=lambda s: (s.span.start_byte, -(s.span.end_byte - s.span.start_byte)))
    enriched: list[SymbolRecord] = []
    stack: list[SymbolRecord] = []
    for symbol in symbols:
        while stack and stack[-1].span.end_byte < symbol.span.start_byte:
            stack.pop()
        parent = stack[-1] if stack and stack[-1].span.start_byte <= symbol.span.start_byte and stack[-1].span.end_byte >= symbol.span.end_byte else None
        enriched.append(SymbolRecord(
            symbol.symbol_id, symbol.name, symbol.kind, symbol.span, symbol.name_span,
            parent.symbol_id if parent else None, symbol.exported, symbol.signature,
        ))
        stack.append(enriched[-1])
    return enriched


def _parse_specifiers(text: str) -> tuple[str, ...]:
    values: list[str] = []
    for item in re.split(r",", text):
        item = item.strip().strip("{}")
        if not item:
            continue
        local = item.split(" as ", 1)[-1].strip()
        values.append(local)
    return tuple(values)


def _extract_imports(tree: ParseTree) -> list[ImportRecord]:
    records: list[ImportRecord] = []
    text = tree.source.decode("utf-8", errors="replace")
    if tree.language in JS_TS_LANGUAGES:
        for match in re.finditer(r"^\s*import\s+(.+?)\s+from\s+[\"']([^\"']+)[\"']", text, re.M):
            imported = _parse_specifiers(match.group(1))
            records.append(ImportRecord(match.group(2), imported, imported, "static", _span_from_text(tree.source, match.start(), match.end())))
        for match in re.finditer(r"^\s*import\s+[\"']([^\"']+)[\"']", text, re.M):
            records.append(ImportRecord(match.group(1), ("*",), (), "side-effect", _span_from_text(tree.source, match.start(), match.end())))
    elif tree.language in PYTHON_LANGUAGES:
        for match in re.finditer(r"^\s*from\s+([^\s]+)\s+import\s+(.+)$", text, re.M):
            imported = _parse_specifiers(match.group(2))
            records.append(ImportRecord(match.group(1), imported, imported, "static", _span_from_text(tree.source, match.start(), match.end())))
        for match in re.finditer(r"^\s*import\s+(.+)$", text, re.M):
            for item in (x.strip() for x in match.group(1).split(",")):
                if not item:
                    continue
                source = item.split(" as ", 1)[0].strip()
                local = item.split(" as ", 1)[1].strip() if " as " in item else source
                records.append(ImportRecord(source, (source,), (local,), "static", _span_from_text(tree.source, match.start(), match.end())))
    return _dedup(records, lambda x: (x.source, x.span.start_byte, x.span.end_byte, x.kind))


def _extract_exports(tree: ParseTree, symbols: list[SymbolRecord]) -> list[SymbolRecord]:
    if tree.language not in JS_TS_LANGUAGES:
        return []
    text = tree.source.decode("utf-8", errors="replace")
    exported_names: set[str] = set()
    for match in re.finditer(r"^\s*export\s+(?:default\s+)?(?:async\s+)?(?:function|class)\s+([A-Za-z_$][\w$]*)", text, re.M):
        exported_names.add(match.group(1))
    for match in re.finditer(r"\bexport\s*\{([^}]+)\}", text):
        exported_names.update(part.split(" as ", 1)[0].strip() for part in match.group(1).split(",") if part.strip())
    return [
        SymbolRecord(s.symbol_id, s.name, s.kind, s.span, s.name_span, s.parent_symbol_id, True, s.signature)
        for s in symbols if s.name in exported_names
    ]


def _context_symbol(span: Span, symbols: list[SymbolRecord]) -> str | None:
    containing = [s for s in symbols if s.span.start_byte <= span.start_byte and s.span.end_byte >= span.end_byte]
    return min(containing, key=lambda s: s.span.end_byte - s.span.start_byte).symbol_id if containing else None


def _extract_references(tree: ParseTree, symbols: list[SymbolRecord], imports: list[ImportRecord]) -> list[ReferenceRecord]:
    excluded_ranges = [(s.name_span.start_byte, s.name_span.end_byte) for s in symbols]
    excluded_ranges += [(i.span.start_byte, i.span.end_byte) for i in imports]
    references: list[ReferenceRecord] = []
    for node in _walk(tree):
        if getattr(node, "type", "") not in IDENTIFIER_TYPES:
            continue
        span = _span(node)
        if any(a <= span.start_byte and span.end_byte <= b for a, b in excluded_ranges):
            continue
        references.append(ReferenceRecord(_text(node, tree.source), "identifier", span, _context_symbol(span, symbols), None))
    return _dedup(references, lambda x: (x.name, x.span.start_byte, x.span.end_byte))


def _extract_calls(tree: ParseTree) -> tuple[list[IntegrationRecord], list[TestRecord]]:
    integrations: list[IntegrationRecord] = []
    tests: list[TestRecord] = []
    text = tree.source.decode("utf-8", errors="replace")
    for node in _walk(tree):
        if getattr(node, "type", "") not in {"call", "call_expression", "new_expression"}:
            continue
        callee = _field(node, "function") or _field(node, "constructor") or _field(node, "method")
        call_text = _text(callee, tree.source) if callee is not None else _text(node, tree.source).split("(", 1)[0]
        base = re.split(r"[.$]", call_text.strip())[-1]
        kind = CALL_INTEGRATIONS.get(base.lower())
        if kind:
            integrations.append(IntegrationRecord(base, kind, _span(node)))
        if base.lower() in {"test", "it", "describe", "suite", "pytest"}:
            framework = "javascript" if tree.language in JS_TS_LANGUAGES else "pytest"
            tests.append(TestRecord(framework, call_text, _span(node)))
    if tree.language == "python":
        for match in re.finditer(r"^\s*def\s+(test_[A-Za-z0-9_]+)\s*\(", text, re.M):
            tests.append(TestRecord("pytest", match.group(1), _span_from_text(tree.source, match.start(), match.end())))
    return _dedup(integrations, lambda x: (x.integration, x.span.start_byte)), _dedup(tests, lambda x: (x.name, x.span.start_byte, x.framework))


def _extract_endpoints(tree: ParseTree) -> list[EndpointRecord]:
    if tree.language not in JS_TS_LANGUAGES | PYTHON_LANGUAGES:
        return []
    text = tree.source.decode("utf-8", errors="replace")
    patterns = [
        ("express", re.compile(r"\b(?:app|router)\.(get|post|put|patch|delete|options|head)\s*\(\s*['\"]([^'\"]+)['\"]", re.I)),
        ("fastapi", re.compile(r"@\w+\.(get|post|put|patch|delete|options|head)\(\s*['\"]([^'\"]+)['\"]", re.I)),
        ("flask", re.compile(r"@\w+\.route\(\s*['\"]([^'\"]+)['\"]", re.I)),
        ("nestjs", re.compile(r"@(Get|Post|Put|Patch|Delete|Options|Head)\(\s*['\"]?([^'\")\s]*)", re.I)),
    ]
    records: list[EndpointRecord] = []
    for framework, pattern in patterns:
        for match in pattern.finditer(text):
            if framework == "flask":
                records.append(EndpointRecord(framework, None, match.group(1), _span_from_text(tree.source, match.start(), match.end())))
            else:
                records.append(EndpointRecord(framework, match.group(1).upper(), match.group(2), _span_from_text(tree.source, match.start(), match.end())))
    return _dedup(records, lambda x: (x.framework, x.method, x.path, x.span.start_byte))


def _extract_queries(tree: ParseTree, symbols: list[SymbolRecord]) -> list[QueryRecord]:
    records: list[QueryRecord] = []
    for node in _walk(tree):
        kind = QUERY_TYPES.get(getattr(node, "type", ""))
        if kind:
            span = _span(node)
            records.append(QueryRecord(kind, _text(node, tree.source), span, _context_symbol(span, symbols)))
    if tree.language in JS_TS_LANGUAGES | PYTHON_LANGUAGES:
        text = tree.source.decode("utf-8", errors="replace")
        for match in re.finditer(r"['\"]((?:SELECT|INSERT|UPDATE|DELETE)\b.+?)['\"]", text, re.I | re.S):
            query = match.group(1).strip()
            span = _span_from_text(tree.source, match.start(), match.end())
            records.append(QueryRecord(query.split(None, 1)[0].upper(), query, span, _context_symbol(span, symbols)))
    return _dedup(records, lambda x: (x.query_kind, x.span.start_byte, x.span.end_byte))


def _extract_configs(tree: ParseTree) -> list[ConfigRecord]:
    records: list[ConfigRecord] = []
    for node in _walk(tree):
        if getattr(node, "type", "") in {"pair", "block_mapping_pair", "flow_pair", "mapping_pair"}:
            key = _field(node, "key") or _field(node, "name") or (node.named_children[0] if getattr(node, "named_children", []) else None)
            if key is not None:
                records.append(ConfigRecord(_text(key, tree.source).strip('"\''), "mapping-key", _span(node)))
    return _dedup(records, lambda x: (x.key, x.span.start_byte))


def _span_from_text(source: bytes, start: int, end: int) -> Span:
    def point(offset: int) -> Position:
        prefix = source[:offset]
        line = prefix.count(b"\n") + 1
        last = prefix.rfind(b"\n")
        return Position(line, offset - (last + 1) + 1)
    return Span(start, end, point(start), point(end))


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
    symbols = _extract_symbols(tree)
    imports = _extract_imports(tree)
    exports = _extract_exports(tree, symbols)
    references = _extract_references(tree, symbols, imports)
    integrations, tests = _extract_calls(tree)
    endpoints = _extract_endpoints(tree)
    queries = _extract_queries(tree, symbols)
    configs = _extract_configs(tree)
    return ParsedFile(
        path=relative_path, language=tree.language, source_sha256=tree.source_sha256,
        byte_length=len(tree.source), root_type=str(tree.root.type), has_errors=tree.has_errors,
        error_count=tree.error_count, ast_nodes=tree.nodes, symbols=tuple(symbols), imports=tuple(imports),
        exports=tuple(exports), references=tuple(references), endpoints=tuple(endpoints), queries=tuple(queries),
        configs=tuple(configs), integrations=tuple(integrations), tests=tuple(tests), limitations=tree.limitations,
    )
