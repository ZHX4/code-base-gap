"""Deserialize a Phase 3 semantic-index JSON document into its domain models."""
from __future__ import annotations

from typing import Any, TypeVar

from code_base_gap.phase3.models import (
    AstNodeRecord, ConfigRecord, EndpointRecord, ImportRecord, IntegrationRecord, ParsedFile,
    Position, QueryRecord, ReferenceRecord, SemanticIndex, Span, SymbolRecord, TestRecord,
)

T = TypeVar("T")


def _position(value: dict[str, Any]) -> Position:
    return Position(int(value["line"]), int(value["column"]))


def _span(value: dict[str, Any]) -> Span:
    return Span(int(value["start_byte"]), int(value["end_byte"]), _position(value["start"]), _position(value["end"]))


def _ast(value: dict[str, Any]) -> AstNodeRecord:
    return AstNodeRecord(
        node_id=int(value["node_id"]),
        parent_id=value.get("parent_id"),
        node_type=str(value["node_type"]),
        named=bool(value["named"]),
        span=_span(value["span"]),
        child_ids=tuple(int(item) for item in value.get("child_ids", [])),
        field_name=value.get("field_name"),
    )


def _symbol(value: dict[str, Any]) -> SymbolRecord:
    return SymbolRecord(
        symbol_id=str(value["symbol_id"]),
        name=str(value["name"]),
        kind=str(value["kind"]),
        span=_span(value["span"]),
        name_span=_span(value.get("name_span", value["span"])),
        parent_symbol_id=value.get("parent_symbol_id"),
        exported=bool(value.get("exported", False)),
        signature=value.get("signature"),
    )


def semantic_index_from_dict(payload: dict[str, Any]) -> SemanticIndex:
    files: list[ParsedFile] = []
    for raw in payload.get("files", []):
        files.append(ParsedFile(
            path=str(raw["path"]),
            language=str(raw["language"]),
            source_sha256=str(raw["source_sha256"]),
            byte_length=int(raw["byte_length"]),
            root_type=str(raw["root_type"]),
            has_errors=bool(raw["has_errors"]),
            error_count=int(raw["error_count"]),
            ast_nodes=tuple(_ast(item) for item in raw.get("ast_nodes", [])),
            symbols=tuple(_symbol(item) for item in raw.get("symbols", [])),
            imports=tuple(ImportRecord(
                source=str(item["source"]),
                imported=tuple(str(x) for x in item.get("imported", [])),
                local_names=tuple(str(x) for x in item.get("local_names", [])),
                kind=str(item["kind"]),
                span=_span(item["span"]),
            ) for item in raw.get("imports", [])),
            exports=tuple(_symbol(item) for item in raw.get("exports", [])),
            references=tuple(ReferenceRecord(
                name=str(item["name"]), kind=str(item["kind"]), span=_span(item["span"]),
                context_symbol_id=item.get("context_symbol_id"), target_hint=item.get("target_hint"),
            ) for item in raw.get("references", [])),
            endpoints=tuple(EndpointRecord(
                framework=str(item["framework"]), method=item.get("method"), path=item.get("path"),
                span=_span(item["span"]), handler_hint=item.get("handler_hint"),
            ) for item in raw.get("endpoints", [])),
            queries=tuple(QueryRecord(
                query_kind=str(item["query_kind"]), text=str(item["text"]), span=_span(item["span"]),
                context_symbol_id=item.get("context_symbol_id"),
            ) for item in raw.get("queries", [])),
            configs=tuple(ConfigRecord(
                key=str(item["key"]), value_kind=str(item["value_kind"]), span=_span(item["span"]),
            ) for item in raw.get("configs", [])),
            integrations=tuple(IntegrationRecord(
                integration=str(item["integration"]), kind=str(item["kind"]), span=_span(item["span"]),
            ) for item in raw.get("integrations", [])),
            tests=tuple(TestRecord(
                framework=item.get("framework"), name=item.get("name"), span=_span(item["span"]),
            ) for item in raw.get("tests", [])),
            limitations=tuple(str(item) for item in raw.get("limitations", [])),
        ))
    index = SemanticIndex(
        schema_version=str(payload.get("schema_version", "phase3.semantic-index.v1")),
        repository_revision=payload.get("repository_revision"),
        files=files,
        limitations=[str(item) for item in payload.get("limitations", [])],
        parser_versions={str(k): str(v) for k, v in payload.get("parser_versions", {}).items()},
    )
    index.finalize()
    return index
