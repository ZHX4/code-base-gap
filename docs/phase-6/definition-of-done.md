# Phase 6 — Definition of Done

## System model

- [x] Canonical system-model schema exists.
- [x] Stable deterministic IDs exist for reconstructed entities.
- [x] Components are reconstructed from repository topology.
- [x] Entry points are reconstructed from explicit Phase 4 endpoint nodes.
- [x] Data-store signals are reconstructed from query evidence.
- [x] External dependencies are reconstructed from integration/external-module evidence.
- [x] Trust-boundary signals are represented explicitly.
- [x] Critical-path candidates are represented conservatively.
- [x] Critical-path steps reference only Phase 6 entities and are self-contained.
- [x] Observed/inferred/unknown provenance is preserved.
- [x] Repository-level framework/deployment/CI/build/test/package-manager signals are preserved without falsely attributing them to components.
- [x] Upstream limitations are preserved.

## Integrity

- [x] Phase 2/Phase 4 immutable revision mismatch is rejected.
- [x] Phase 4 input requires an immutable repository revision.
- [x] Duplicate Phase 4 node and edge identifiers are rejected.
- [x] Phase 4 orphan edges are rejected by the loader.
- [x] Duplicate Phase 6 entity identifiers are rejected.
- [x] Model references are validated before serialization.
- [x] Output ordering is deterministic.
- [x] JSON schema is machine-readable.

## Interface

- [x] Strict JSON input loaders exist.
- [x] Python API exists.
- [x] CLI exists.
- [x] Packaging entry point is registered.

## Testing

- [x] Component reconstruction test.
- [x] Entry-point reconstruction test.
- [x] Data-store reconstruction test.
- [x] External-dependency reconstruction test.
- [x] Repository-level signal preservation test.
- [x] Revision mismatch test.
- [x] Orphan-edge input test.
- [x] Duplicate-node input test.
- [x] Critical-path self-containment test.
- [x] Reproducibility test.
- [x] Structural validator.

## Explicit boundary

Phase 6 does not claim compiler-grade architecture recovery, runtime topology, business-logic requirements, threat-model completeness, vulnerability detection, LLM reasoning, dynamic verification, or remediation.

CI is intentionally excluded from phase completion criteria.
