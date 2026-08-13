# Phase 1 — Product Definition

## 1. Product name

Working name: **Code Base Gap**.

Technical product category: **Autonomous Unified Repository Auditor**.

## 2. Problem statement

Existing software-analysis workflows are fragmented across code review, SAST, software-composition analysis, secret scanners, infrastructure scanners, tests, DAST, and human architectural/security review. These tools are valuable but generally answer bounded questions. Code Base Gap is intended to correlate those signals and reason about the software system as a whole.

The product targets findings that can be difficult to express as a single static rule, including:

- Missing authorization or security controls.
- Missing validation, transaction, rollback, idempotency, or audit behavior.
- Inconsistent controls across services or endpoints.
- Business-logic vulnerabilities.
- Security invariants that appear intended but are not enforced.
- Critical paths with insufficient tests.
- Dangerous assumptions between services.
- Reliability and correctness gaps that can become security or integrity incidents.
- Root causes spanning multiple files or components.

## 3. Primary user

The initial user is an engineer, security engineer, maintainer, or technical researcher responsible for auditing an existing repository.

Primary use cases:

1. Run a full repository audit at a pinned commit.
2. Understand the architecture and trust boundaries inferred by the auditor.
3. Review prioritized findings with evidence.
4. Separate confirmed findings from hypotheses and unverified areas.
5. Generate and validate remediation.
6. Re-audit after a fix or commit.

## 4. Product promise

The product promises **systematic, evidence-backed auditing**, not perfect vulnerability detection.

The product must never claim:

- That all vulnerabilities were found.
- That an inferred requirement is definitely a business requirement unless it is explicitly documented.
- That an LLM-generated hypothesis is confirmed without sufficient evidence.
- That a numerical coverage score means semantic completeness.

## 5. Scope for V1

### Included

- Git repositories and local repositories.
- Public repositories first; private repositories after secure credential handling is implemented.
- TypeScript / JavaScript.
- Python.
- SQL.
- Docker.
- YAML / JSON.
- Web applications and backend services.
- Repository-wide static analysis.
- Existing test discovery and selected test execution.
- Security, reliability, architecture, and quality gap analysis.
- Evidence-backed reporting.

### Explicitly out of scope for V1

- Kernel-level auditing.
- Embedded firmware.
- Native mobile application analysis as a first-class target.
- Full binary reverse engineering.
- Guaranteed production-environment discovery.
- Autonomous deployment of fixes to production.
- Automatic exploitation of arbitrary real-world targets.

## 6. Finding classes

Every finding belongs to at least one class:

- `security`
- `reliability`
- `correctness`
- `architecture`
- `quality`
- `testing`
- `dependency`
- `configuration`
- `supply_chain`

Subclasses are extensible and must not require changing the fundamental finding envelope.

## 7. Finding lifecycle

```text
observed
  -> hypothesized
  -> investigating
  -> verified / likely / unverified / rejected
  -> reported
  -> remediating
  -> fixed / regression
```

A result must retain its prior states in provenance; the latest state must not erase history.

## 8. Trust model

The system treats all repository material as untrusted data, including:

- Source code.
- README and documentation.
- Comments.
- Test fixtures.
- Build scripts.
- Package lifecycle scripts.
- Generated code.
- Configuration.
- Containers.
- Dependencies.

Repository content must never become privileged instructions to the auditor merely because an agent read it.

## 9. Core quality attributes

### Correctness
Deterministic analyses must be reproducible for the same repository revision, tool versions, and configuration.

### Evidence
Every high-impact conclusion must cite concrete evidence and analysis provenance.

### Explainability
The final user-facing result must explain what was observed, why it matters, what was checked, and what remains uncertain.

### Safety
Untrusted code must run only inside explicitly isolated execution environments.

### Resumability
Long audits must survive individual worker failures and resume from checkpoints.

### Incrementality
Future phases must support reusing existing analysis when only a bounded graph region changes.

### Extensibility
New languages, scanners, LLM providers, graph backends, and verification engines must be adapters, not invasive rewrites.

## 10. Success criteria for the complete product

The final product is considered successful only when it can:

1. Ingest a supported repository at an immutable revision.
2. Produce a machine-readable repository/system model.
3. Correlate deterministic tool results with repository-level reasoning.
4. Detect both explicit vulnerabilities and meaningful missing controls/gaps.
5. Generate verification plans for important hypotheses.
6. Independently verify or reject important findings when feasible.
7. Preserve evidence and provenance for every reported conclusion.
8. Report measurable coverage and explicit blind spots.
9. Generate remediation and regression validation for supported findings.
10. Operate securely and reliably as a production service.

## 11. Non-functional goals

The final platform should be:

- Multi-tenant capable.
- Horizontally scalable.
- Observable.
- Auditable.
- Secure by default.
- Cost-aware.
- Reproducible.
- API-first.
- CI/CD friendly.
