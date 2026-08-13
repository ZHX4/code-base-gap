# Phase 1 — System Architecture

## 1. Architectural objective

Code Base Gap is a layered system in which deterministic program analysis, repository intelligence, AI reasoning, and controlled runtime verification cooperate. No single layer is authoritative for every question.

```text
                         Web UI / CLI / CI
                                  |
                           API / Auth Layer
                                  |
                         Audit Orchestrator
                                  |
       +--------------------------+---------------------------+
       |                          |                           |
 Repository Intelligence    Deterministic Analysis      Runtime Sandbox
       |                          |                           |
       |                    CodeQL / Semgrep                 |
       |                    SCA / Secrets / IaC              |
       |                          |                           |
       +--------------------------+---------------------------+
                                  |
                         Unified Evidence Bus
                                  |
                     System Knowledge / Graph
                                  |
              +-------------------+-------------------+
              |                   |                   |
         Architecture         Security          Reliability
            Agent               Agent               Agent
              |                   |                   |
              +-------------------+-------------------+
                                  |
                       Invariant / Contract Layer
                                  |
                         GAP / Hypothesis Engine
                                  |
                         Verification Engine
                                  |
                         Counter-Analysis Agent
                                  |
                            Judge / Ranker
                                  |
                       Finding + Provenance Store
                                  |
                    Remediation + Regression Check
                                  |
                           Audit History
```

## 2. Major subsystems

### 2.1 Repository Gateway

Responsibilities:

- Accept repository references and local sources.
- Pin the exact revision being audited.
- Build a safe local workspace.
- Record source provenance.
- Reject malformed or unsupported inputs early.

### 2.2 Reconnaissance Engine

Responsibilities:

- Detect languages, frameworks, package managers, build systems, test frameworks, CI/CD, and deployment hints.
- Locate source roots, generated material, configuration, documentation, and likely entry points.
- Produce a repository manifest.

### 2.3 Parsing and Semantic Index

Responsibilities:

- Parse supported languages.
- Extract ASTs and symbols.
- Resolve imports/exports and references.
- Identify functions, classes, methods, routes, queries, configuration, tests, and external integrations.

### 2.4 Program Knowledge Graph

The graph is the canonical relationship model used by higher-level agents. It must be versioned by audited revision.

Node examples:

```text
Repository, Commit, File, Module, Symbol, Function, Class,
Endpoint, Parameter, Database, Table, Column, Service, Queue,
Dependency, Package, Config, EnvironmentVariable, Secret, Role,
Permission, Test, Container, ExternalService, TrustBoundary
```

Edge examples:

```text
CONTAINS
IMPORTS
EXPORTS
CALLS
READS
WRITES
REACHES
EXPOSES
AUTHENTICATES
AUTHORIZES
DEPENDS_ON
CONFIGURED_BY
TESTED_BY
DEPLOYS_TO
SENDS_TO
RECEIVES_FROM
CROSSES_TRUST_BOUNDARY
```

Edges must carry provenance when the relationship was inferred rather than directly observed.

### 2.5 Deterministic Analysis Adapters

Each external analyzer is wrapped behind a stable internal adapter. Initial candidates include:

- CodeQL.
- Semgrep.
- SCA/OSV-based dependency analysis.
- Gitleaks.
- Trivy.
- Checkov.
- OWASP ZAP.

The internal platform must not depend on a vendor-specific output format.

### 2.6 Evidence Bus

Every tool output, source observation, graph relation, runtime observation, generated test, and model conclusion enters a common provenance layer.

Evidence is immutable once attached to a completed audit result. Corrections create new evidence records rather than mutating history.

### 2.7 Reasoning Agents

Agents are role-specialized. They share the same evidence and knowledge graph rather than independently reconstructing the repository.

Initial roles:

- Architecture Agent.
- Security Agent.
- Reliability Agent.
- Quality Agent.
- Dependency/Supply-chain Agent.
- Configuration Agent.
- Testing Agent.
- Threat Modeling Agent.
- Gap Agent.
- Verification Agent.
- Counter Agent.
- Judge Agent.

### 2.8 Invariant / Contract Layer

The system stores explicit and inferred system expectations.

Each invariant records:

- statement;
- source;
- type (`explicit`, `inferred`, `unknown`);
- affected scope;
- supporting evidence;
- confidence;
- status.

### 2.9 Verification Engine

Verification chooses the lowest-cost reliable method first:

```text
repository evidence
 -> graph/static proof
 -> generated test
 -> isolated runtime test
 -> DAST/fuzz/browser verification
```

Only feasible and safe verification actions are executed.

### 2.10 Judge / Ranker

The judge combines:

- supporting evidence;
- counter-evidence;
- deterministic analyzer output;
- runtime observations;
- exploitability;
- impact;
- reachability;
- asset criticality;
- uncertainty.

The judge may downgrade or reject an otherwise compelling agent hypothesis.

## 3. Data flow

```text
source
  -> repository manifest
  -> parsed representation
  -> semantic index
  -> graph
  -> deterministic findings
  -> system reconstruction
  -> invariants
  -> hypotheses
  -> verification
  -> counter-evidence
  -> judged findings
  -> remediation
```

## 4. Storage boundaries

PostgreSQL is the initial system of record. It stores metadata, state, findings, provenance, and graph relationships. A specialized graph database may be introduced later only if measurements demonstrate a need.

Redis is an ephemeral cache/coordination layer and must never be the only copy of durable audit state.

Object storage holds large immutable artifacts such as source snapshots, logs, traces, reports, and generated evidence bundles.

## 5. LLM boundary

LLMs are non-authoritative reasoning components.

LLMs may:

- summarize;
- synthesize;
- infer candidate invariants;
- generate hypotheses;
- propose tests;
- prioritize;
- explain evidence.

LLMs must not silently:

- invent tool output;
- invent runtime observations;
- convert untrusted repository text into privileged instructions;
- mark a high-impact issue as confirmed without required evidence.

## 6. Model-provider abstraction

A model router will be used in later phases. The architecture must not couple core domain logic to one model provider. Requests should describe a task class and constraints; provider selection belongs to the routing layer.

## 7. External tool boundary

All external analyzers are executed via explicit adapters that produce normalized observations. Tool version, invocation configuration, exit status, and relevant raw artifact references must be stored.

## 8. Security boundaries

The primary boundaries are:

1. User -> public API.
2. API -> orchestrator.
3. Orchestrator -> untrusted repository worker.
4. Untrusted worker -> network and host resources.
5. Worker -> external analysis tools.
6. Analysis artifacts -> LLM context.
7. Tenant A -> tenant B.
8. Runtime sandbox -> control plane.

No component running untrusted repository code may share unconstrained host privileges with the control plane.

## 9. Failure model

The system assumes:

- network failures;
- tool crashes;
- malformed repositories;
- unsupported syntax;
- dependency installation failures;
- runtime test failures;
- model timeouts;
- provider outages;
- rate limits;
- partial graph construction;
- inconsistent tool outputs.

Every long-running phase must be resumable and idempotent where possible.

## 10. Architectural constraints

- Core domain models must be provider-independent.
- Evidence records are append-only.
- Audit execution is stateful and resumable.
- Repository revisions are immutable audit targets.
- Untrusted code cannot run in the API process.
- High-impact findings require independent evidence paths whenever feasible.
- Every reported result must be traceable to an auditable evidence set.
