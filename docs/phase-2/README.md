# Phase 2 — Repository Ingestion & Reconnaissance

Phase 2 turns an external repository reference into a pinned, machine-readable repository manifest and reconnaissance report.

## Outputs

1. **Repository revision** — immutable commit SHA selected for the audit.
2. **Safe workspace metadata** — local working directory is an implementation detail; no repository code executes during Phase 2.
3. **Repository manifest** — deterministic file inventory, exclusions, counts, and repository metadata.
4. **Reconnaissance report** — languages, frameworks, package managers, build systems, tests, CI/CD, deployment hints, configuration and documentation signals.
5. **Limitations** — unsupported or unreadable material is explicitly recorded.

## Security rules

- Repository content is untrusted data.
- No build, test, package-install, lifecycle script, container, or repository hook is executed in Phase 2.
- Git operations use non-interactive configuration, disable recursive submodules, and use explicit timeouts.
- Symlinks are inventoried but not followed during filesystem scanning.
- `.git` and dependency/build output directories are excluded from the source inventory and recorded as exclusions.
- Maximum file count and per-file byte limits are enforced.

## Supported V1 reconnaissance targets

- TypeScript / JavaScript
- Python
- SQL
- Docker
- YAML / JSON
- Web applications and backend services

## CLI

```bash
python -m code_base_gap.phase2.cli /path/to/repository --output audit.json
python -m code_base_gap.phase2.cli https://github.com/org/repository.git --ref main --output audit.json
```

Phase 2 does not parse ASTs, build the knowledge graph, run SAST, execute tests, or invoke LLMs. Those are later phases.
