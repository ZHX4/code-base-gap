#!/usr/bin/env python3
"""Pure filesystem inventory for Phase 2; never executes repository content."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

EXCLUDED = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build", "coverage", ".next", ".nuxt", ".turbo", ".cache", "target"}
LANG = {".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript", ".py": "Python", ".pyi": "Python", ".sql": "SQL", ".json": "JSON", ".jsonc": "JSON", ".yaml": "YAML", ".yml": "YAML"}
SPECIAL = {"Dockerfile": "Docker", "Makefile": "Make"}
TEST = re.compile(r"(^|[/._-])(test|tests|spec|specs)([/._-]|$)", re.I)
GEN = re.compile(r"(^|[/._-])(generated|gen|vendor|dist|build)([/._-]|$)", re.I)
CONFIG = {"package.json", "pyproject.toml", "requirements.txt", "requirements-dev.txt", "poetry.lock", "Pipfile", "Pipfile.lock", "setup.py", "tsconfig.json", "jsconfig.json", "Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml", "vercel.json", "fly.toml", "render.yaml", "Procfile"}
DOC_EXT = {".md", ".rst", ".adoc", ".txt"}


def inventory(root: Path, max_files: int = 100_000) -> dict:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")
    files, exclusions, limitations = [], [], []
    total_bytes = 0
    stop = False
    for current, dirs, names in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        rel_current = current_path.relative_to(root).as_posix() if current_path != root else ""
        kept = []
        for directory in sorted(dirs):
            if directory in EXCLUDED:
                exclusions.append(f"{rel_current}/{directory}".strip("/"))
            else:
                kept.append(directory)
        dirs[:] = kept
        for name in sorted(names):
            path = current_path / name
            rel = path.relative_to(root).as_posix()
            stat = path.lstat()
            suffix = path.suffix.lower()
            language = SPECIAL.get(name) or LANG.get(suffix)
            kind = "source" if language in {"TypeScript", "JavaScript", "Python", "SQL"} else "other"
            if name in CONFIG or suffix in {".json", ".jsonc", ".yaml", ".yml", ".toml", ".ini", ".cfg"} or name.startswith(".env"):
                kind = "config"
            elif suffix in DOC_EXT:
                kind = "documentation"
            files.append({"path": rel, "size_bytes": stat.st_size, "extension": suffix, "language": language, "kind": kind, "is_test": bool(TEST.search(rel)), "is_generated": bool(GEN.search(rel)), "is_config": kind == "config", "is_documentation": kind == "documentation", "is_symlink": path.is_symlink()})
            total_bytes += stat.st_size
            if len(files) >= max_files:
                limitations.append(f"file inventory limit reached: {max_files}")
                stop = True
                break
        if stop:
            break
    stats = {"file_count": len(files), "total_bytes": total_bytes, "source_files": sum(x["kind"] == "source" for x in files), "config_files": sum(x["is_config"] for x in files), "documentation_files": sum(x["is_documentation"] for x in files), "test_files": sum(x["is_test"] for x in files), "symlinks": sum(x["is_symlink"] for x in files)}
    return {"files": files, "exclusions": sorted(set(exclusions)), "limitations": sorted(set(limitations)), "stats": stats}


def write_json(data: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
