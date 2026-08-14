# Phase 2 — Repository Ingestion & Reconnaissance

Phase 2 turns a repository reference into a pinned, machine-readable repository manifest and deterministic reconnaissance report.

## Implemented outputs

1. **Repository revision** — a 40-character commit SHA for public GitHub sources when a ref can be resolved. Local repositories use their `.git/HEAD`/packed-ref metadata when available and otherwise report `unversioned`.
2. **Safe workspace** — remote GitHub repositories are downloaded as a pinned ZIP archive into an isolated temporary directory. Local repositories are read in place without executing repository content.
3. **Repository manifest** — deterministic file inventory, exclusion list, size/count statistics, source/config/test/documentation classification, and immutable configuration metadata.
4. **Reconnaissance report** — languages, common frameworks, package managers, build systems, tests, CI/CD, deployment signals, source roots, likely entry points, configuration, documentation, and limitations.
5. **Machine-readable contracts** — `spec/schemas/phase2-manifest.schema.json` and `spec/schemas/phase2-reconnaissance.schema.json`.

## Security guarantees of Phase 2

Repository content is untrusted data.

Phase 2 **never** runs repository code. It does not execute builds, tests, package managers, lifecycle scripts, Git hooks, containers, or application servers.

Filesystem scanning does not follow symlink directories. Common VCS metadata, dependency trees, caches, generated/build directories, and other high-volume material are excluded from the source inventory and recorded as exclusions.

Public GitHub archive acquisition is pinned to a resolved commit SHA before extraction. Archive extraction rejects absolute paths, traversal paths, symlink entries, excessive entry counts, excessive uncompressed size, and archives exceeding the configured compressed-size limit.

All Phase 2 resource limits are configurable and must be positive:

```text
max_files
max_file_bytes
max_total_bytes
max_archive_bytes
```

## CLI

```bash
python -m code_base_gap.phase2.cli /path/to/repository --output audit.json
python -m code_base_gap.phase2.cli https://github.com/org/repository.git --ref main --output audit.json
```

or after package installation:

```bash
code-base-gap /path/to/repository --output audit.json
```

## Phase boundary

Phase 2 intentionally does not parse ASTs, build the program knowledge graph, run SAST/SCA, execute tests, invoke LLMs, or perform dynamic verification. Those are later phases.
