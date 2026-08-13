# Phase 1 — Audit State Machine

The audit lifecycle is a durable state machine. An implementation may add internal sub-states, but these externally meaningful states must remain stable.

## 1. States

```text
CREATED
QUEUED
PREPARING
INGESTING
RECONNAISSANCE
PARSING
INDEXING
GRAPH_BUILDING
BASELINE_ANALYSIS
SYSTEM_RECONSTRUCTION
CONTRACT_DISCOVERY
GAP_ANALYSIS
HYPOTHESIS_ANALYSIS
VERIFICATION
COUNTER_ANALYSIS
JUDGING
REPORTING
REMEDIATION
REVALIDATION
COMPLETED
PARTIAL
FAILED
CANCELLED
```

## 2. State requirements

### CREATED

Audit record exists and is immutable with respect to repository revision.

Allowed transitions:

```text
CREATED -> QUEUED
CREATED -> CANCELLED
```

### QUEUED

Waiting for an available worker.

```text
QUEUED -> PREPARING
QUEUED -> CANCELLED
```

### PREPARING

Validate configuration, resource policy, tool availability, and safe workspace.

```text
PREPARING -> INGESTING
PREPARING -> FAILED
```

### INGESTING

Acquire and pin the repository revision.

```text
INGESTING -> RECONNAISSANCE
INGESTING -> FAILED
```

### RECONNAISSANCE

Discover languages, frameworks, build systems, tests, CI/CD, and deployment hints.

```text
RECONNAISSANCE -> PARSING
RECONNAISSANCE -> PARTIAL
RECONNAISSANCE -> FAILED
```

### PARSING

Parse supported content and record unsupported/failed files explicitly.

```text
PARSING -> INDEXING
PARSING -> PARTIAL
PARSING -> FAILED
```

### INDEXING

Create semantic indexes and symbol/reference information.

```text
INDEXING -> GRAPH_BUILDING
INDEXING -> PARTIAL
INDEXING -> FAILED
```

### GRAPH_BUILDING

Build versioned system knowledge graph.

```text
GRAPH_BUILDING -> BASELINE_ANALYSIS
GRAPH_BUILDING -> PARTIAL
GRAPH_BUILDING -> FAILED
```

### BASELINE_ANALYSIS

Run deterministic analyzers and normalize observations.

```text
BASELINE_ANALYSIS -> SYSTEM_RECONSTRUCTION
BASELINE_ANALYSIS -> PARTIAL
BASELINE_ANALYSIS -> FAILED
```

### SYSTEM_RECONSTRUCTION

Build architecture, trust-boundary, service, endpoint, and data-flow models.

```text
SYSTEM_RECONSTRUCTION -> CONTRACT_DISCOVERY
SYSTEM_RECONSTRUCTION -> PARTIAL
SYSTEM_RECONSTRUCTION -> FAILED
```

### CONTRACT_DISCOVERY

Identify explicit and inferred invariants.

```text
CONTRACT_DISCOVERY -> GAP_ANALYSIS
CONTRACT_DISCOVERY -> PARTIAL
CONTRACT_DISCOVERY -> FAILED
```

### GAP_ANALYSIS

Search for missing controls, inconsistencies, and system-level weaknesses.

```text
GAP_ANALYSIS -> HYPOTHESIS_ANALYSIS
GAP_ANALYSIS -> PARTIAL
GAP_ANALYSIS -> FAILED
```

### HYPOTHESIS_ANALYSIS

Generate and scope claims requiring verification.

```text
HYPOTHESIS_ANALYSIS -> VERIFICATION
HYPOTHESIS_ANALYSIS -> COUNTER_ANALYSIS
HYPOTHESIS_ANALYSIS -> PARTIAL
```

### VERIFICATION

Use static, generated-test, runtime, DAST, browser, or fuzzing techniques when feasible.

```text
VERIFICATION -> COUNTER_ANALYSIS
VERIFICATION -> JUDGING
VERIFICATION -> PARTIAL
```

### COUNTER_ANALYSIS

Attempt to disprove or downgrade important hypotheses.

```text
COUNTER_ANALYSIS -> JUDGING
COUNTER_ANALYSIS -> PARTIAL
```

### JUDGING

Resolve evidence, severity, confidence, status, and root cause.

```text
JUDGING -> REPORTING
JUDGING -> PARTIAL
```

### REPORTING

Persist final findings, coverage, limitations, and provenance.

```text
REPORTING -> REMEDIATION
REPORTING -> COMPLETED
```

### REMEDIATION

Optional patch/test generation and validation.

```text
REMEDIATION -> REVALIDATION
REMEDIATION -> COMPLETED
```

### REVALIDATION

Re-run relevant checks after remediation.

```text
REVALIDATION -> COMPLETED
REVALIDATION -> PARTIAL
```

### COMPLETED

No further audit execution occurs. Historical audit data remains immutable.

### PARTIAL

The audit completed with explicitly documented limitations. A partial audit must never be reported as full coverage.

### FAILED

The audit could not produce a valid result. Failure reason and recovery data must be persisted.

### CANCELLED

Execution was intentionally stopped. Partial artifacts remain available unless retention policy deletes them.

## 3. Recovery rule

Every transition must persist a checkpoint containing:

```text
state
state_version
input_references
output_references
started_at
completed_at
error
retry_count
worker_identity
```

A retry must be idempotent or detect an already-completed checkpoint before repeating expensive work.

## 4. Failure classification

Failures are classified as:

- `transient`
- `configuration`
- `unsupported`
- `security_block`
- `resource_limit`
- `tool_failure`
- `model_failure`
- `repository_failure`
- `internal_bug`

Only retryable classes may be automatically retried.

## 5. Cancellation rule

Cancellation must stop new work, allow safe cleanup, preserve completed artifacts, and transition to `CANCELLED` rather than pretending the audit completed.
