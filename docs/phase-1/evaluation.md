# Phase 1 — Evaluation Strategy

The evaluation plan is designed before implementation so later phases can be judged objectively.

## 1. Evaluation layers

### Layer A — Contract correctness

Validate that all domain objects satisfy the schemas and lifecycle rules defined in Phase 1.

### Layer B — Tool correctness

For each analyzer adapter, validate normalization, provenance, version capture, exit-state handling, and failure classification.

### Layer C — System-model correctness

Use repositories with known architecture, endpoints, dependencies, and trust boundaries to measure reconstruction accuracy.

### Layer D — Finding quality

Measure precision, recall, false-positive rate, false-negative rate, verification rate, and root-cause accuracy.

### Layer E — Operational quality

Measure audit duration, resource consumption, retry behavior, resumability, cost, and reproducibility.

## 2. Benchmark categories

The benchmark must eventually contain:

- Known CVEs.
- Known GitHub security advisories.
- Real-world authorization flaws.
- Injection vulnerabilities.
- Secret exposure cases.
- Dependency vulnerabilities.
- Configuration mistakes.
- Missing security controls.
- Business-logic vulnerabilities.
- Transaction/rollback gaps.
- Idempotency gaps.
- Reliability failures.
- Architecture inconsistencies.
- Missing critical tests.
- Cross-service trust failures.

## 3. Baselines

The system must be evaluated against at least:

1. Deterministic scanners alone.
2. LLM-only repository reasoning.
3. Deterministic scanners plus basic LLM summarization.
4. Code Base Gap with full verification/counter-analysis.

Specific tools will be selected and version-pinned during Phase 19.

## 4. Primary metrics

### Precision

```text
true_positives / (true_positives + false_positives)
```

### Recall

```text
true_positives / (true_positives + false_negatives)
```

### F1

Harmonic mean of precision and recall.

### False-positive rate

Reported findings that ground truth rejects.

### Verification success rate

Percentage of hypotheses for which the system obtains a reliable verification outcome.

### Root-cause accuracy

Whether the reported root cause identifies the actual enabling condition rather than only a downstream symptom.

### Coverage

Measured independently across the dimensions defined in `contracts.md`.

### Reproducibility

Percentage of findings that can be reproduced from the same pinned revision and toolchain manifest.

### Operational cost

Track:

- wall-clock duration;
- CPU time;
- memory peak;
- storage used;
- model tokens/cost;
- external tool time.

## 5. Calibration

Confidence values must be evaluated for ranking and calibration. Until calibration is demonstrated, the UI must describe confidence as an internal confidence score rather than a probability of correctness.

## 6. Ablation studies

The research/engineering evaluation should measure the value of each layer:

```text
LLM only
+ graph
+ deterministic tools
+ invariants
+ verification
+ counter-agent
+ judge
```

The objective is to identify which components materially improve finding quality and cost.

## 7. Regression rule

A change that improves one benchmark category but causes a material regression in confirmed-finding precision or safety must not be merged without explicit review.

## 8. Benchmark governance

Ground-truth cases must record:

```text
case_id
repository
revision
expected_issue
severity
ground_truth_evidence
verification_method
source
license/usage_basis
```

Benchmark cases must be versioned. Scores must always identify the benchmark version and tool/model versions.
