# Phase 4 — Program Knowledge Graph

Phase 4 converts the Phase 3 semantic index into a deterministic, queryable program knowledge graph.

## Graph scope

The graph currently models:

- repository;
- files;
- modules;
- symbols;
- endpoints;
- queries;
- configuration keys;
- integrations;
- tests;
- unresolved external modules.

## Relationships

- `CONTAINS`
- `DECLARES`
- `IMPORTS`
- `EXPORTS`
- `RESOLVES_TO`
- `EXPOSES`
- `EXECUTES_QUERY`
- `USES_CONFIG`
- `INTEGRATES_WITH`
- `TESTS`
- `LOCATED_IN`

Every edge must reference nodes that already exist. Node/edge IDs are deterministic SHA-256-derived identifiers, so the same semantic input produces the same graph identity.

## Resolution policy

Phase 4 is intentionally conservative. It resolves an import only when exactly one repository-relative candidate exists. Identifier references are resolved only when the target is unambiguous. Ambiguous or unresolved relationships are not fabricated.

External imports become `external_module` nodes so the graph preserves dependency boundaries without pretending that an external package is repository code.

## CLI

Create a Phase 3 semantic index first:

```bash
code-base-gap-parse /path/to/repository --output semantic-index.json
```

Then build the graph:

```bash
code-base-gap-graph semantic-index.json --output program-graph.json
```

The Python API is:

```python
from code_base_gap.phase4 import build_program_graph

graph = build_program_graph(semantic_index)
```

## Determinism and safety

Phase 4 does not execute repository code. It only transforms Phase 3 data. Graph serialization is normalized by sorted node/edge IDs and sorted limitations.

## Explicit boundary

Phase 4 does not implement:

- SAST/SCA;
- dynamic execution;
- LLM reasoning;
- vulnerability discovery;
- threat modeling;
- complete compiler-grade name/type resolution;
- remediation.

Those belong to later phases.
