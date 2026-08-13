# Phase 1 — Definition of Done

Phase 1 is complete only when every item below exists, is internally consistent, and is treated as normative for implementation phases.

## Product

- [x] Product name and category defined.
- [x] Core problem defined.
- [x] Primary user and use cases defined.
- [x] V1 scope defined.
- [x] Explicit non-goals defined.
- [x] Product promise and limitations defined.
- [x] Finding categories defined.
- [x] Quality attributes defined.

## Architecture

- [x] High-level architecture defined.
- [x] Major subsystems defined.
- [x] Repository/system knowledge graph concept defined.
- [x] Deterministic tool adapter boundary defined.
- [x] Evidence bus/provenance concept defined.
- [x] Agent roles defined.
- [x] Invariant/contract layer defined.
- [x] Verification and counter-analysis layers defined.
- [x] Storage boundaries defined.
- [x] LLM boundary defined.
- [x] Failure model defined.

## Domain contracts

- [x] Audit identity defined.
- [x] Audit profile defined.
- [x] Observation contract defined.
- [x] Evidence contract defined.
- [x] Invariant contract defined.
- [x] Hypothesis contract defined.
- [x] Finding contract defined.
- [x] Finding fingerprint semantics defined.
- [x] Agent execution metadata defined.
- [x] Tool invocation metadata defined.
- [x] Location semantics defined.
- [x] Coverage semantics defined.
- [x] Audit-result envelope defined.
- [x] Evidence precedence guidance defined.
- [x] No-hallucinated-evidence rule defined.

## Audit lifecycle

- [x] Canonical audit states defined.
- [x] State transitions defined.
- [x] Checkpoint requirements defined.
- [x] Retry/failure classification defined.
- [x] Cancellation semantics defined.
- [x] Partial-audit semantics defined.

## Security

- [x] Assets identified.
- [x] Trust zones identified.
- [x] Threat actors identified.
- [x] Major threat categories identified.
- [x] Platform security invariants defined.
- [x] Abuse cases defined.
- [x] Security review gates defined.

## Evaluation

- [x] Evaluation layers defined.
- [x] Benchmark categories defined.
- [x] Baseline comparison strategy defined.
- [x] Primary metrics defined.
- [x] Confidence/calibration policy defined.
- [x] Ablation strategy defined.
- [x] Regression policy defined.
- [x] Benchmark governance defined.

## Phase 1 exit criteria

Phase 1 can be considered exited only when:

1. A developer starting Phase 2 can implement repository ingestion without inventing the product model.
2. A developer implementing findings can use one stable finding/evidence contract.
3. A developer implementing orchestration can follow the audit state machine without redefining lifecycle semantics.
4. A security engineer can identify the intended trust boundaries and major threats.
5. An evaluator can design objective tests from the documented metrics and benchmark strategy.
6. The repository README points to the authoritative Phase 1 documents.

## Explicit non-claims

Completion of Phase 1 does **not** mean:

- the product can audit repositories yet;
- security scanning is implemented;
- an LLM agent exists;
- a sandbox is production hardened;
- findings are accurate yet;
- the product is production ready.

Those are later phase deliverables.
