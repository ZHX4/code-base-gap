# Phase 1 — Architecture Decisions

## ADR-001 — Product is a repository auditor, not a PR reviewer

**Decision:** The primary audit unit is an immutable repository revision. PR review is a later integration surface.

**Reason:** The product differentiator is system-level understanding, cross-file reasoning, and detection of missing controls that may not appear in a diff.

## ADR-002 — Deterministic analysis and AI reasoning are complementary

**Decision:** Existing program-analysis/security tools are integrated behind adapters. The product's proprietary layer focuses on system reconstruction, correlation, gap detection, hypothesis generation, verification, and evidence reasoning.

**Reason:** Reimplementing mature scanners would add large engineering cost without improving the core differentiator.

## ADR-003 — PostgreSQL is the initial system of record

**Decision:** Start with PostgreSQL for durable metadata, findings, provenance, and graph relationships. Add a specialized graph database only after benchmarks show a concrete need.

**Reason:** Avoid premature infrastructure complexity while retaining a path to a dedicated graph store.

## ADR-004 — LLMs are non-authoritative

**Decision:** LLM output is a reasoning artifact. High-impact confirmation requires supporting evidence and, when feasible, independent verification.

**Reason:** Prevent hallucinated findings and unsupported claims from becoming security decisions.

## ADR-005 — Repository content is hostile input

**Decision:** Repository files, comments, documentation, scripts, tests, and generated files are treated as untrusted data.

**Reason:** Prompt injection and malicious build/test behavior are expected attack classes.

## ADR-006 — Evidence is append-only

**Decision:** Evidence attached to audit conclusions is immutable. Corrections create new evidence and new state.

**Reason:** Preserve provenance and enable reproducibility and forensic review.

## ADR-007 — Coverage is multidimensional

**Decision:** Never represent audit completeness as a single unsupported percentage. Coverage is reported separately for files, symbols, endpoints, flows, authorization paths, tests, runtime surfaces, dependencies, and configuration.

**Reason:** A single number can conceal large blind spots.

## ADR-008 — Verification is a first-class subsystem

**Decision:** Hypothesis generation and finding confirmation are separate stages.

**Reason:** The system should actively seek evidence and attempt to disprove high-impact claims rather than converting model confidence directly into severity.

## ADR-009 — V1 language scope is intentionally constrained

**Decision:** V1 targets TypeScript/JavaScript, Python, SQL, Docker, YAML, and JSON for web/backend repositories.

**Reason:** This is broad enough to demonstrate system-level auditing while keeping parser, runtime, and framework coverage tractable.

## ADR-010 — Production readiness is a platform property

**Decision:** Accuracy alone does not qualify a release as production ready. Security isolation, reliability, observability, recovery, reproducibility, benchmark evidence, and operational controls are mandatory.

**Reason:** The auditor itself becomes a security-critical service when processing untrusted customer repositories.
