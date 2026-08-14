"""Machine-serializable domain models for Phase 3."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SUPPORTED_LANGUAGES = (
    "javascript", "typescript", "tsx", "python", "sql", "json", "yaml", "dockerfile",
)


@dataclass(frozen=True)
class SemanticIndexConfig:
    max_files: int = 100_000
    max_file_bytes: int = 2_000_000
    max_total_bytes: int = 256_000_000
    max_ast_nodes_per_file: int = 200_000
    max_ast_depth: int = 1_000
    max_source_text_bytes: int = 2_000_000


@dataclass(frozen=True)
class Position:
    line: int
    column: int


@dataclass(frozen=True)
class Span:
    start_byte: int
    end_byte: int
    start: Position
    end: Position


@dataclass(frozen=True)
class AstNodeRecord:
    node_id: int
    parent_id: int | None
    node_type: str
    named: bool
    span: Span
    child_ids: tuple[int, ...]
    field_name: str | None = None


@dataclass(frozen=True)
class SymbolRecord:
    symbol_id: str
    name: str
    kind: str
    span: Span
    name_span: Span
    parent_symbol_id: str | None = None
    exported: bool = False
    signature: str | None = None


@dataclass(frozen=True)
class ReferenceRecord:
    name: str
    kind: str
    span: Span
    context_symbol_id: str | None = None
    target_hint: str | None = None


@dataclass(frozen=True)
class ImportRecord:
    source: str
    imported: tuple[str, ...]
    local_names: tuple[str, ...]
    kind: str
    span: Span


@dataclass(frozen=True)
class EndpointRecord:
    framework: str
    method: str | None
    path: str | None
    span: Span
    handler_hint: str | None = None


@dataclass(frozen=True)
class QueryRecord:
    query_kind: str
    text: str
    span: Span
    context_symbol_id: str | None = None


@dataclass(frozen=True)
class ConfigRecord:
    key: str
    value_kind: str
    span: Span


@dataclass(frozen=True)
class IntegrationRecord:
    integration: str
    kind: str
    span: Span


@dataclass(frozen=True)
class TestRecord:
    framework: str | None
    name: str | None
    span: Span


@dataclass(frozen=True)
class ParsedFile:
    path: str
    language: str
    source_sha256: str
    byte_length: int
    root_type: str
    has_errors: bool
    error_count: int
    ast_nodes: tuple[AstNodeRecord, ...]
    symbols: tuple[SymbolRecord, ...]
    imports: tuple[ImportRecord, ...]
    exports: tuple[SymbolRecord, ...]
    references: tuple[ReferenceRecord, ...]
    endpoints: tuple[EndpointRecord, ...]
    queries: tuple[QueryRecord, ...]
    configs: tuple[ConfigRecord, ...]
    integrations: tuple[IntegrationRecord, ...]
    tests: tuple[TestRecord, ...]
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SemanticIndex:
    schema_version: str = "phase3.semantic-index.v1"
    repository_revision: str | None = None
    files: list[ParsedFile] = field(default_factory=list)
    symbol_count: int = 0
    reference_count: int = 0
    import_count: int = 0
    endpoint_count: int = 0
    query_count: int = 0
    config_count: int = 0
    integration_count: int = 0
    test_count: int = 0
    limitations: list[str] = field(default_factory=list)
    parser_versions: dict[str, str] = field(default_factory=dict)

    def finalize(self) -> None:
        self.symbol_count = sum(len(f.symbols) for f in self.files)
        self.reference_count = sum(len(f.references) for f in self.files)
        self.import_count = sum(len(f.imports) for f in self.files)
        self.endpoint_count = sum(len(f.endpoints) for f in self.files)
        self.query_count = sum(len(f.queries) for f in self.files)
        self.config_count = sum(len(f.configs) for f in self.files)
        self.integration_count = sum(len(f.integrations) for f in self.files)
        self.test_count = sum(len(f.tests) for f in self.files)

    def to_dict(self) -> dict[str, Any]:
        self.finalize()
        return asdict(self)
