# Phase 5 — Deterministic Analysis Layer

Phase 5 converts the repository workspace into normalized, deterministic analysis findings.

## Scope

- Built-in secret-pattern analysis.
- Built-in dangerous-code pattern analysis.
- Built-in infrastructure configuration checks.
- Semgrep adapter with SARIF normalization.
- Gitleaks adapter with SARIF normalization.
- Trivy adapter for vulnerability/misconfiguration/secret scanning.
- Syft adapter for SBOM discovery.
- CodeQL discovery adapter; database creation/build execution is intentionally deferred to the isolated execution/sandbox phase.
- Deterministic finding fingerprints and de-duplication.
- Tool/version/provenance metadata.
- JSON report schema and CLI.

## Safety boundary

Phase 5 does not execute repository build scripts, package-install hooks, test suites, application servers, or arbitrary shell commands. External tools are invoked only through an allowlisted, shell-free runner with fixed adapter arguments.

Missing tools are reported as limitations. Their absence never becomes a false claim that analysis was performed.

## Usage

```bash
python -m code_base_gap.phase5.cli /path/to/workspace --output scan.json --no-external-tools
```

With installed external analyzers:

```bash
python -m code_base_gap.phase5.cli /path/to/workspace --output scan.json
```
