"""Deterministic, non-executing repository filesystem inspection."""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from .models import FileEntry

EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", "node_modules", ".venv", "venv", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build", "coverage",
    ".next", ".nuxt", ".turbo", ".cache", "target", "vendor",
}
LANGUAGE_BY_SUFFIX = {
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".mts": "TypeScript", ".cts": "TypeScript",
    ".py": "Python", ".pyi": "Python", ".sql": "SQL", ".dockerfile": "Docker",
    ".json": "JSON", ".jsonc": "JSON", ".yaml": "YAML", ".yml": "YAML",
    ".toml": "TOML",
}
SPECIAL_LANGUAGE = {"Dockerfile": "Docker", "Containerfile": "Docker", "Makefile": "Make"}
TEST_RE = re.compile(r"(^|[/._-])(test|tests|spec|specs)([/._-]|$)", re.I)
GENERATED_RE = re.compile(r"(^|[/._-])(generated|gen|vendor|dist|build)([/._-]|$)", re.I)
CONFIG_NAMES = {
    "package.json", "pyproject.toml", "requirements.txt", "requirements-dev.txt", "poetry.lock",
    "Pipfile", "Pipfile.lock", "setup.py", "setup.cfg", "tox.ini", "pytest.ini", "tsconfig.json",
    "jsconfig.json", "Dockerfile", "Containerfile", "docker-compose.yml", "docker-compose.yaml",
    "compose.yml", "compose.yaml", "vercel.json", "fly.toml", "render.yaml", "Procfile",
    "Makefile", "CMakeLists.txt", "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "build.gradle.kts",
}
DOC_EXTENSIONS = {".md", ".rst", ".adoc", ".txt"}


def safe_relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def file_sha256(path: Path, max_bytes: int = 2_000_000) -> str | None:
    if path.is_symlink() or not path.is_file():
        return None
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            remaining = max_bytes
            while remaining:
                chunk = handle.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                digest.update(chunk)
                remaining -= len(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def inventory(root: Path, max_files: int, max_file_bytes: int, max_total_bytes: int) -> tuple[list[FileEntry], list[str], list[str]]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")
    files: list[FileEntry] = []
    exclusions: list[str] = []
    limitations: list[str] = []
    total_bytes = 0

    for current, dirs, names in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        kept: list[str] = []
        for directory in sorted(dirs):
            if directory in EXCLUDED_DIRS:
                exclusions.append(safe_relpath(current_path / directory, root))
            else:
                kept.append(directory)
        dirs[:] = kept

        for name in sorted(names):
            path = current_path / name
            rel = safe_relpath(path, root)
            try:
                stat = path.lstat()
            except OSError as exc:
                limitations.append(f"unreadable:{rel}:{type(exc).__name__}")
                continue
            is_symlink = path.is_symlink()
            suffix = path.suffix.lower()
            language = SPECIAL_LANGUAGE.get(name) or LANGUAGE_BY_SUFFIX.get(suffix)
            if name.lower() == "dockerfile":
                language = "Docker"
            is_config = (
                name in CONFIG_NAMES or suffix in {".json", ".jsonc", ".yaml", ".yml", ".toml", ".ini", ".cfg"}
                or name.startswith(".env")
            )
            is_doc = suffix in DOC_EXTENSIONS
            kind = "source" if language in {"JavaScript", "TypeScript", "Python", "SQL"} else "other"
            if is_config:
                kind = "config"
            elif is_doc:
                kind = "documentation"
            is_test = bool(TEST_RE.search(rel))
            is_generated = bool(GENERATED_RE.search(rel))
            size = int(stat.st_size)
            if len(files) >= max_files:
                limitations.append(f"file_count_limit:{max_files}")
                return files, sorted(set(exclusions)), sorted(set(limitations))
            if not is_symlink and size > max_file_bytes:
                limitations.append(f"file_size_limit:{rel}:{size}")
                continue
            if total_bytes + size > max_total_bytes:
                limitations.append(f"total_bytes_limit:{max_total_bytes}")
                return files, sorted(set(exclusions)), sorted(set(limitations))
            files.append(FileEntry(rel, size, suffix, language, kind, is_test, is_generated, is_config, is_doc, is_symlink))
            total_bytes += size
    return files, sorted(set(exclusions)), sorted(set(limitations))
