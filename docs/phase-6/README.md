# Phase 6 — System Reconstruction Engine

Phase 6 reconstructs a deterministic repository-level system model from the immutable Phase 2 reconnaissance artifact and Phase 4 program knowledge graph.

## Responsibilities

- Reconstruct application/service/package/library/infrastructure components from repository topology.
- Identify HTTP entry points and associate them with components when evidence exists.
- Reconstruct data-store interaction signals from query nodes.
- Reconstruct external-module and integration dependencies.
- Infer trust-boundary signals for ingress, external services, and databases.
- Assemble conservative critical-path candidates from explicit graph relationships.
- Preserve observed vs inferred vs unknown provenance.
- Preserve limitations from all upstream phases.
- Produce deterministic, machine-readable output.

## Non-responsibilities

Phase 6 does not perform:

- LLM reasoning;
- threat modeling beyond deterministic boundary signals;
- invariant discovery;
- vulnerability detection;
- dynamic execution;
- verification;
- remediation.

Those responsibilities belong to later phases.

## Inputs

1. Phase 2 result JSON.
2. Phase 4 program-knowledge-graph JSON.

Both artifacts must refer to the same immutable repository revision.

## Usage

```bash
code-base-gap-reconstruct \
  --reconnaissance audit.json \
  --graph program-graph.json \
  --output system-model.json
```

The generated model uses schema `phase6.system-model.v1`.
