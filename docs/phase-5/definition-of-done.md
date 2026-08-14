# Phase 5 — Definition of Done

## Canonical model

- [x] Unified finding model.
- [x] Unified location/evidence model.
- [x] Tool execution provenance.
- [x] Deterministic finding fingerprints.
- [x] Finding de-duplication.
- [x] Severity and confidence fields.

## Deterministic analysis

- [x] Built-in secret detection.
- [x] Built-in dangerous-code patterns.
- [x] Built-in infrastructure configuration patterns.
- [x] Semgrep adapter.
- [x] Gitleaks adapter.
- [x] Trivy vulnerability/misconfiguration/secret adapter.
- [x] Syft SBOM adapter.
- [x] CodeQL discovery adapter with build execution explicitly deferred to Phase 18.
- [x] SARIF normalization.

## Safety

- [x] External tools are allowlisted.
- [x] No shell execution.
- [x] Tool arguments contain no repository-controlled executable command strings.
- [x] Tool timeouts exist.
- [x] Tool output limits exist.
- [x] Repository code is not built, installed, tested, or launched by Phase 5.
- [x] Missing tools produce explicit limitations.

## Output

- [x] Machine-readable report schema.
- [x] CLI.
- [x] Stable finding fingerprints.
- [x] Tool/version/provenance metadata.
- [x] Deterministic normalized output.

## Validation

- [x] Structural validator.
- [x] Unit tests for fingerprints and de-duplication.
- [x] Unit tests for secret and dangerous-pattern detection.
- [x] Unit tests for SARIF normalization.
- [x] Unit tests for runner allowlisting and missing tools.
- [x] Unit tests for report output.

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
