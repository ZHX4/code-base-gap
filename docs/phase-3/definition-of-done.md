# Phase 3 — Definition of Done

Phase 3 is complete when the repository contains a deterministic parsing and semantic-indexing implementation that is usable by Phase 4 without depending on parser internals.

## Parsing

- [x] Tree-sitter runtime is pinned to the supported 0.26.x API range.
- [x] Supported grammars are installed through a reproducible language-pack version.
- [x] JavaScript is parsed.
- [x] TypeScript is parsed.
- [x] TSX is parsed.
- [x] Python is parsed.
- [x] SQL is parsed.
- [x] JSON is parsed.
- [x] YAML is parsed.
- [x] Dockerfile is parsed.
- [x] Syntax errors are retained as metadata rather than silently discarded.

## Resource safety

- [x] All semantic-index resource limits require positive integers.
- [x] File-size limits cannot exceed the source-text or repository-total limits.
- [x] AST node and depth limits are propagated to semantic extraction.
- [x] Each semantic traversal is bounded by the parser-declared limits.
- [x] Large files are skipped with explicit limitations.

## AST

- [x] AST nodes have stable per-file IDs.
- [x] Parent-child relationships are materialized.
- [x] Field names are retained where available.
- [x] Source byte and line/column spans are retained.

## Semantic index

- [x] Symbols are extracted.
- [x] Symbol declaration spans and name-only spans are distinguished.
- [x] Nested symbol containment is represented.
- [x] Imports are extracted by supported language family.
- [x] Imported names and local aliases are represented separately.
- [x] Exports are extracted where statically observable.
- [x] Identifier references are extracted without excluding symbol bodies.
- [x] Reference context can point to the containing symbol.
- [x] Endpoint candidates are extracted.
- [x] SQL/query candidates are extracted.
- [x] Configuration keys are extracted.
- [x] External integration candidates are extracted.
- [x] Test candidates are extracted.
- [x] Heuristic-derived records remain structurally identifiable by their record type and provenance span.

## Safety

- [x] Phase 3 never executes repository code.
- [x] Symlinks are never followed.
- [x] Repository-relative path containment is checked before reading files.
- [x] Absolute and unsafe relative manifest paths are rejected.
- [x] Existing Phase 2 file/total-size limits remain available.
- [x] Manifest revision and explicitly requested revision must agree.
- [x] Indexing limitations are explicitly recorded.

## Interfaces

- [x] Python API is available through `code_base_gap.phase3`.
- [x] CLI is available through `code_base_gap.phase3.cli`.
- [x] Machine-readable semantic-index schema is present.
- [x] Parser implementation is hidden behind Phase 3 models/pipeline from later phases.

## Validation

- [x] Structural validator checks all Phase 3 modules and schema contracts.
- [x] Unit tests cover language detection, Python, TypeScript, SQL, syntax errors, resource limits, bounded AST traversal, import aliases, references, and symlink safety.
- [x] CI is intentionally excluded from Phase 3 completion criteria for this repository.

## Explicit phase boundary

Phase 3 does not claim to implement:

- a program knowledge graph;
- complete name resolution;
- compiler-grade type checking;
- SAST/SCA;
- LLM reasoning;
- dynamic execution;
- vulnerability verification;
- remediation.
