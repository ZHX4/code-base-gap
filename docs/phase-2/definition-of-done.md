# Phase 2 — Definition of Done

Phase 2 is complete when the repository contains a runnable implementation that converts a supported repository source into a pinned manifest and deterministic reconnaissance report without executing repository content.

## Source handling

- [x] Local directories are supported.
- [x] Public HTTPS GitHub repositories are supported.
- [x] GitHub refs are resolved to immutable commit SHAs before archive acquisition.
- [x] Unsupported remote schemes are rejected.
- [x] Malformed GitHub identifiers are rejected.
- [x] Local Git HEAD/packed-ref metadata is read without executing repository hooks.

## Safety

- [x] Repository build/test/install scripts are never executed.
- [x] Repository containers are never started.
- [x] Filesystem scans do not follow directory symlinks.
- [x] Archive traversal is rejected.
- [x] Archive symlink entries are rejected.
- [x] Archive compressed-size limits are enforced.
- [x] Archive entry-count limits are enforced.
- [x] Archive uncompressed-size limits are enforced before extraction.
- [x] File-count and file-size limits are enforced.
- [x] Total extracted source size is bounded.

## Manifest

- [x] Deterministic file inventory is produced.
- [x] Source/configuration/documentation/test/generated classifications are recorded.
- [x] Exclusions are recorded.
- [x] Limitations are recorded.
- [x] Repository revision and source kind are recorded.
- [x] Execution policy explicitly records that Phase 2 performs no code execution.

## Reconnaissance

- [x] Languages are detected from inventory.
- [x] Common JavaScript/TypeScript frameworks are detected from package metadata.
- [x] Common Python frameworks are detected from package metadata.
- [x] Package managers are detected from lock/package metadata.
- [x] Build systems are detected from repository markers.
- [x] Test frameworks/signals are detected without running tests.
- [x] CI/CD systems are detected from configuration markers.
- [x] Deployment platforms are detected from configuration markers.
- [x] Source roots are reported.
- [x] Likely entry points are reported as candidates, not guarantees.
- [x] Configuration and documentation files are reported.

## Interfaces

- [x] Python API is available through `code_base_gap.phase2`.
- [x] CLI is available through `python -m code_base_gap.phase2.cli`.
- [x] Installed console script is registered as `code-base-gap`.
- [x] JSON output is deterministic and machine-readable.
- [x] Phase 2 manifest and reconnaissance schemas are present.

## Validation

- [x] Structural validator parses every Phase 2 Python module with `ast`.
- [x] Structural validator checks Phase 2 schema presence and JSON validity.
- [x] Unit tests cover parsing, inventory, limits, local pipeline behavior, and execution policy.
- [ ] Remote end-to-end test requires external network access and is intentionally not a prerequisite of this repository-only implementation review.

## Phase boundary

Phase 2 must not claim to implement:

- AST parsing.
- Semantic indexing.
- Program knowledge graph construction.
- SAST/SCA.
- LLM reasoning.
- Dynamic application execution.
- Security verification.

Those belong to later phases.
