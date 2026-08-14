# Phase 5 — Definition of Done

Phase 5 is complete when deterministic security/quality analyzers can inspect an already-ingested repository workspace without executing project code, normalize their results into a stable evidence-backed report, and preserve important analysis artifacts.

## Canonical model

- [x] Unified finding model.
- [x] Unified location/evidence model.
- [x] Tool execution provenance.
- [x] Deterministic finding fingerprints.
- [x] Finding de-duplication.
- [x] Severity and confidence fields.
- [x] Repository-relative evidence locations only.
- [x] Tool raw stdout/stderr excluded from serialized reports.

## Deterministic analysis

- [x] Built-in secret detection.
- [x] Built-in dangerous-code patterns.
- [x] Built-in infrastructure configuration patterns.
- [x] Scanner file-size and file-count bounds.
- [x] Generated/dependency directory exclusions.
- [x] Semgrep adapter.
- [x] Gitleaks adapter with bounded temporary SARIF handling.
- [x] Trivy vulnerability/misconfiguration/secret adapter.
- [x] Syft SBOM adapter.
- [x] Syft SBOM persisted as a report artifact when successfully generated.
- [x] CodeQL discovery adapter with build execution explicitly deferred to Phase 18.
- [x] SARIF normalization with safe repository-relative locations.
- [x] Malformed/unsupported SARIF is rejected rather than silently accepted.

## Safety

- [x] External tools are allowlisted.
- [x] No shell execution.
- [x] Tool arguments contain no repository-controlled executable command strings.
- [x] Tool timeouts exist.
- [x] Tool output limits exist.
- [x] External report/artifact size limits exist.
- [x] Repository code is not built, installed, tested, or launched by Phase 5.
- [x] Missing tools produce explicit limitations.
- [x] Absolute, URI, and traversal-style finding locations are rejected.

## Output

- [x] Machine-readable report schema.
- [x] CLI.
- [x] Stable finding fingerprints.
- [x] Tool/version/provenance metadata.
- [x] Deterministic normalized output.
- [x] Analysis artifacts can be persisted in the report.

## Validation

- [x] Structural validator.
- [x] Unit tests for fingerprints and de-duplication.
- [x] Unit tests for secret and dangerous-pattern detection.
- [x] Unit tests for scanner bounds and exclusions.
- [x] Unit tests for SARIF normalization and unsafe locations.
- [x] Unit tests for runner allowlisting and report redaction.
- [x] Unit tests for report output/artifact contract.

## Explicit boundary

Phase 5 does not claim:

- complete vulnerability detection;
- compiler-grade analysis;
- CodeQL database creation through arbitrary project builds;
- dynamic analysis;
- LLM reasoning;
- verification of findings;
- remediation.

CI is intentionally excluded from Phase 5 completion criteria.
