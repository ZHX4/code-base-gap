# Phase 4 — Definition of Done

Phase 4 is complete when a Phase 3 semantic index can be converted into a deterministic, validated, machine-readable program knowledge graph that later phases can query without depending on Tree-sitter internals.

## Graph model

- [x] Canonical node model exists.
- [x] Canonical edge model exists.
- [x] Stable deterministic node IDs exist.
- [x] Stable deterministic edge IDs exist.
- [x] Node/edge kind contracts are closed and schema-backed.
- [x] Orphan edges are rejected.
- [x] Node/edge ID collisions are rejected.

## Nodes

- [x] Repository nodes.
- [x] File nodes.
- [x] Module nodes.
- [x] Symbol nodes.
- [x] Endpoint nodes.
- [x] Query nodes.
- [x] Configuration nodes.
- [x] Integration nodes.
- [x] Test nodes.
- [x] External-module nodes for unresolved imports.

## Relationships

- [x] Repository containment.
- [x] File/module containment.
- [x] File/symbol declaration.
- [x] Export relationships.
- [x] Import relationships.
- [x] Conservative cross-file import resolution.
- [x] Conservative identifier-reference resolution.
- [x] Endpoint exposure.
- [x] Query ownership/execution relationships.
- [x] Configuration usage relationships.
- [x] Integration relationships.
- [x] Test relationships where a unique name-based target exists.
- [x] Explicit unresolved/ambiguous relationships are not fabricated.

## Query and serialization

- [x] Deterministic query helpers exist.
- [x] JSON serialization exists.
- [x] Serialized nodes and edges are normalized by ID.
- [x] Graph statistics are emitted.
- [x] Machine-readable JSON Schema exists.
- [x] CLI exists.
- [x] Phase 3 semantic-index JSON loader exists for CLI use.

## Safety

- [x] Phase 4 does not execute repository code.
- [x] It consumes Phase 3 data only.
- [x] Unresolved external dependencies are represented explicitly.
- [x] Ambiguous reference resolution is left unresolved.

## Validation

- [x] Structural validator exists.
- [x] Unit tests cover graph integrity.
- [x] Unit tests cover cross-file imports.
- [x] Unit tests cover reference resolution.
- [x] Unit tests cover endpoints/exports.
- [x] Unit tests cover collision handling.
- [x] Unit tests cover deterministic queries.

## Explicit boundary

Phase 4 does not claim to provide:

- compiler-grade type/name resolution;
- complete call-graph construction;
- SAST/SCA;
- dynamic execution;
- LLM reasoning;
- vulnerability discovery;
- verification;
- remediation.
