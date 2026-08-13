# Code Base Gap

Code Base Gap is an autonomous repository auditing platform designed to reason about software systems at repository scale rather than only reviewing individual diffs or running isolated scanners.

## Mission

Given an untrusted software repository, the system should reconstruct a useful model of the system, combine deterministic program-analysis tools with AI reasoning, discover vulnerabilities and missing controls ("gaps"), verify important hypotheses, challenge its own findings, and produce evidence-backed audit results.

The long-term target is a production-grade **Autonomous Unified Repository Auditor**. It must not claim to find every possible bug. Instead, every audit must expose its evidence, verification status, coverage, uncertainty, and limitations.

## Current status

- **Phase 1 — Product Definition & Technical Specification:** complete.
- **Phase 2+ — Implementation:** not started.

The authoritative Phase 1 specification lives under [`docs/phase-1/`](docs/phase-1/).

## Core principles

1. **Repository-level reasoning:** the unit of analysis is the system, not a single file.
2. **Deterministic first:** use parsers and program-analysis engines whenever a deterministic answer is possible.
3. **AI for reasoning:** use language models for synthesis, hypothesis generation, semantic reasoning, and prioritization rather than as the sole source of truth.
4. **Evidence before claims:** no high-impact finding should rely only on an LLM assertion.
5. **Independent verification:** important findings must be statically or dynamically verified when feasible.
6. **Counter-analysis:** high-impact findings must be challenged before they are reported as confirmed.
7. **Explicit uncertainty:** the auditor must distinguish confirmed, likely, unverified, rejected, and out-of-scope results.
8. **Untrusted repositories:** repository code, documentation, scripts, dependencies, and generated artifacts are hostile input until proven otherwise.
9. **Reproducibility:** an audit must be tied to an immutable repository revision and preserve enough provenance to reproduce its conclusions.
10. **No completeness theater:** coverage numbers and confidence scores must have explicit definitions.

## Supported V1 target

The initial product scope is intentionally constrained to:

- Web applications and backend services.
- TypeScript / JavaScript.
- Python.
- SQL.
- Docker.
- YAML / JSON configuration.

The platform architecture must remain extensible to additional languages and runtimes later.

## High-level lifecycle

```text
Repository
  -> Ingest
  -> Reconnaissance
  -> Parse / Index
  -> Build System Graph
  -> Run Deterministic Analysis
  -> Reconstruct Architecture / Contracts
  -> Discover Gaps / Generate Hypotheses
  -> Verify
  -> Counter-analyze
  -> Judge / Rank
  -> Report Evidence
  -> Remediate
  -> Verify Fix
  -> Remember / Incremental Re-audit
```

## Phase roadmap

1. Product Definition & Technical Specification
2. Repository Ingestion & Reconnaissance
3. Code Parsing & Semantic Indexing
4. Program Knowledge Graph
5. Deterministic Analysis Layer
6. System Reconstruction Engine
7. Architecture & Security Reasoning Agents
8. Invariant & Contract Discovery
9. GAP Detection Engine
10. Hypothesis Generation
11. Verification Engine
12. Counter-Analysis & Self-Critique
13. Finding Intelligence Layer
14. Evidence & Audit Provenance
15. Remediation Engine
16. Coverage & Audit Completeness
17. Audit Memory & Incremental Analysis
18. Secure Execution & Sandbox Infrastructure
19. Evaluation & Benchmarking
20. Core Orchestration Platform
21. Production Backend
22. Production Database & Storage
23. Production Web Application
24. CLI & Developer Workflow
25. GitHub/GitLab Integration
26. CI/CD Integration
27. Security of the Auditor
28. Reliability & Observability
29. Performance & Scalability
30. Production Hardening
31. Closed Beta
32. External Validation
33. Release Candidate
34. Production Launch
35. Post-Launch Continuous Improvement

Each phase has a definition of done. Phase completion does not permit silently weakening contracts from previous phases.
