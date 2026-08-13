# Phase 1 — Domain Contracts

These contracts are normative. Later implementation phases may extend them but must not silently change their semantics.

## 1. Audit identity

An audit is uniquely identified by:

```text
project_id
repository_revision
configuration_hash
analysis_profile
```

The repository revision must be immutable for the lifetime of the audit.

## 2. Audit profile

An audit profile describes requested capabilities without exposing implementation details to users.

Required fields:

```text
profile_id
profile_version
languages
analysis_categories
verification_policy
resource_policy
model_policy
```

## 3. Observation contract

An observation is a raw or normalized fact produced by deterministic tooling or repository inspection.

Required fields:

```text
observation_id
observation_type
source_kind
source_reference
repository_revision
location
payload
created_at
tool_name
tool_version
invocation_id
```

An observation must distinguish directly observed facts from derived interpretations.

## 4. Evidence contract

Evidence is the smallest durable unit used to justify a conclusion.

Required fields:

```text
 evidence_id
 evidence_type
 repository_revision
 source_reference
 locator
 excerpt_or_artifact_reference
 provenance
 generated_at
```

Evidence types include:

- `source_code`
- `ast`
- `symbol`
- `call_graph`
- `data_flow`
- `tool_result`
- `configuration`
- `documentation`
- `test`
- `runtime_observation`
- `generated_test`
- `dependency_metadata`
- `graph_relation`
- `model_claim`

A model claim can be evidence for another model step only when its provenance identifies the supporting evidence; it is never equivalent to direct runtime or source evidence by default.

## 5. Invariant contract

```text
invariant_id
statement
category
origin: explicit | inferred | unknown
scope
supporting_evidence[]
confidence
status: active | challenged | rejected
```

Example:

```text
statement: "A normal user can modify only resources they own."
origin: explicit
scope: API resources
```

## 6. Hypothesis contract

```text
hypothesis_id
category
statement
affected_scope
supporting_evidence[]
expected_observations[]
verification_plan
priority
status
```

A hypothesis is not a finding until it reaches the required evidence threshold.

## 7. Finding contract

Every finding must have:

```text
finding_id
fingerprint
repository_revision
category
subcategory
title
summary
impact
severity
confidence
status
affected_components[]
affected_locations[]
root_cause
supporting_evidence[]
counter_evidence[]
verification
remediation
coverage_context
created_at
updated_at
```

### Severity

Allowed values:

```text
critical
high
medium
low
informational
```

Severity is about potential impact, not certainty.

### Confidence

A numeric confidence is paired with a qualitative state:

```text
confirmed
likely
unverified
rejected
```

Confidence must not be presented as a mathematically calibrated probability unless later benchmarking demonstrates calibration.

### Verification

```text
status: not_attempted | planned | running | passed | failed | inconclusive
methods[]
artifacts[]
reproduction_reference
```

### Remediation

```text
recommendation
patch_reference
regression_test_reference
validation_status
```

## 8. Finding fingerprint

The fingerprint must remain stable across re-audits when the logical root cause is unchanged. It should combine normalized information such as:

```text
category
root_cause identity
primary symbols/components
normalized source scope
```

Line numbers alone must not define identity.

## 9. Agent execution contract

Every agent invocation must record:

```text
agent_run_id
agent_role
model_provider
model_id
prompt_policy_version
tool_policy_version
input_context_references
tool_calls[]
output_reference
started_at
completed_at
status
error
```

The implementation must persist enough metadata to reproduce the decision context without storing secrets.

## 10. Tool invocation contract

```text
tool_invocation_id
tool_name
tool_version
arguments_hash
execution_environment
started_at
completed_at
exit_code
stdout_reference
stderr_reference
artifact_references[]
```

Raw arguments must be redacted before persistence if they contain secrets.

## 11. Location contract

Locations must be precise enough for a human to inspect.

```text
repository_revision
file_path
start_line
end_line
symbol
```

Line ranges may be absent when a finding concerns a graph-level or configuration-level issue.

## 12. Coverage contract

Coverage is a structured object, not one magic percentage.

Required dimensions:

```text
files
symbols
endpoints
data_flows
auth_paths
tests
runtime_surfaces
dependencies
configuration
```

Each dimension must contain:

```text
eligible
analyzed
unknown
unsupported
```

## 13. Audit result contract

A completed audit contains:

```text
aud_it_summary
system_model_reference
findings[]
coverage
limitations[]
verification_summary
cost_summary
toolchain_manifest
```

## 14. Evidence hierarchy

When evidence conflicts, use this default precedence, subject to domain-specific rules:

```text
Observed runtime behavior
> deterministic static/data-flow analysis
> directly inspected source/configuration
> derived graph relation
> generated test result
> model inference
> model speculation
```

This hierarchy is not absolute for every question; the final judge must preserve the disagreement rather than hiding it.

## 15. No hallucinated evidence rule

An output is invalid if it claims:

- a file was read when it was not read;
- a command was executed when it was not executed;
- a vulnerability was reproduced when there is no runtime artifact;
- a tool produced a result it did not produce;
- a line or symbol exists without source evidence.

The implementation must make these conditions mechanically detectable wherever possible.
