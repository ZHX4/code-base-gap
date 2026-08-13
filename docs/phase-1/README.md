# Phase 1 — Specification Index

Phase 1 is the authoritative foundation for all subsequent implementation work.

## Documents

| Document | Purpose |
|---|---|
| `product-definition.md` | Product scope, users, non-goals, quality attributes, and success criteria |
| `architecture.md` | System layers, boundaries, graph, evidence flow, and failure model |
| `contracts.md` | Normative domain contracts and evidence rules |
| `audit-state-machine.md` | Canonical audit lifecycle and recovery semantics |
| `threat-model.md` | Assets, trust zones, threats, security invariants, and abuse cases |
| `evaluation.md` | Benchmarks, baselines, metrics, ablations, and regression policy |
| `definition-of-done.md` | Phase completion criteria and explicit non-claims |

## Machine-readable contracts

- `spec/schemas/audit.schema.json`
- `spec/schemas/evidence.schema.json`
- `spec/schemas/finding.schema.json`
- `spec/schemas/hypothesis.schema.json`
- `spec/schemas/invariant.schema.json`

## Normative rules

1. Later implementation phases may extend contracts but must preserve their semantics.
2. High-impact findings require evidence and must not be reported as confirmed from model output alone.
3. Repository revisions are immutable audit targets.
4. Repository content is untrusted input, not privileged agent instructions.
5. Coverage must be multidimensional and explicit.
6. The final product must expose uncertainty and limitations.

## Phase gate

Phase 2 may begin only after the Phase 1 Definition of Done is satisfied and the machine-readable contracts validate as syntactically valid JSON Schema documents.
