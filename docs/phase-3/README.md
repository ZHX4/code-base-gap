# Phase 3 — Code Parsing & Semantic Indexing

Phase 3 converts the Phase 2 repository inventory into a deterministic, machine-readable semantic index. It parses supported source/configuration files with Tree-sitter and extracts AST structure plus semantic records required by later graph and reasoning phases.

## Supported languages

- JavaScript
- TypeScript
- TSX
- Python
- SQL
- JSON
- YAML
- Dockerfile

## Outputs

Each indexed file contains:

- source SHA-256;
- parser language;
- parse root type;
- syntax-error metadata;
- bounded AST node records with parent/child relationships and source spans;
- symbols and nested symbol relationships;
- imports and exports;
- identifier references;
- HTTP endpoint candidates;
- SQL queries;
- configuration keys;
- external integration calls;
- test candidates;
- explicit parsing/indexing limitations.

The repository-level result contains aggregate counts and parser-version metadata.

## Design rules

1. Repository code is data. Nothing is executed by Phase 3.
2. Symlinks are preserved as skipped records and never followed.
3. AST size and depth are bounded.
4. Source-file size and repository total-size limits remain enforced.
5. Deterministic AST facts are separated from heuristic semantic extraction.
6. Later phases consume the semantic index instead of depending directly on Tree-sitter APIs.
7. Every indexed file is identified by a source SHA-256 and repository-relative path.

## CLI

```bash
python -m code_base_gap.phase3.cli /path/to/repository --output semantic-index.json
```

or after installation:

```bash
code-base-gap-parse /path/to/repository --output semantic-index.json
```

Phase 3 does not implement the program knowledge graph, SAST, LLM reasoning, dynamic execution, verification, or remediation. Those are later phases.
