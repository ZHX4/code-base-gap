"""Deterministic reconnaissance over the Phase 2 manifest; never executes repository code."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Iterable

from .filesystem import CONFIG_NAMES, file_sha256
from .models import AuditManifest, FileEntry, ReconnaissanceReport


def _read_text(path: Path, limit: int = 512_000) -> str:
    try:
        with path.open("rb") as handle:
            data = handle.read(limit + 1)
        if len(data) > limit:
            data = data[:limit]
        return data.decode("utf-8", errors="replace")
    except OSError:
        return ""


def _json(path: Path) -> dict:
    try:
        value = json.loads(_read_text(path))
        return value if isinstance(value, dict) else {}
    except (ValueError, TypeError):
        return {}


def _add_once(items: list[str], *values: str) -> None:
    for value in values:
        if value and value not in items:
            items.append(value)


def _relative_parent(path: str) -> str:
    parent = Path(path).parent.as_posix()
    return "." if parent == "." else parent


def _detect_frameworks(root: Path, files: list[FileEntry], report: ReconnaissanceReport) -> None:
    package = root / "package.json"
    if package.is_file():
        data = _json(package)
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        framework_map = {
            "next": "Next.js", "react": "React", "vue": "Vue", "nuxt": "Nuxt",
            "express": "Express", "fastify": "Fastify", "nestjs": "NestJS", "@nestjs/core": "NestJS",
            "svelte": "Svelte", "@remix-run/node": "Remix", "hono": "Hono", "koa": "Koa",
        }
        for package_name, framework in framework_map.items():
            if package_name in deps:
                _add_once(report.frameworks, framework)
        _add_once(report.package_managers, "npm" if (root / "package-lock.json").is_file() else "")
        _add_once(report.package_managers, "pnpm" if (root / "pnpm-lock.yaml").is_file() else "")
        _add_once(report.package_managers, "yarn" if (root / "yarn.lock").is_file() else "")
        if data.get("scripts"):
            _add_once(report.build_systems, "package.json scripts")
            for script_name in data["scripts"]:
                if script_name in {"build", "compile"}:
                    _add_once(report.build_systems, "JavaScript build scripts")
                if script_name in {"test", "test:unit", "test:e2e"}:
                    _add_once(report.test_frameworks, "package.json test scripts")

    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        text = _read_text(pyproject).lower()
        _add_once(report.package_managers, "Python packaging (pyproject.toml)")
        for marker, framework in {
            "django": "Django", "fastapi": "FastAPI", "flask": "Flask", "starlette": "Starlette",
            "pydantic": "Pydantic", "sqlalchemy": "SQLAlchemy",
        }.items():
            if marker in text:
                _add_once(report.frameworks, framework)
        if "pytest" in text:
            _add_once(report.test_frameworks, "pytest")

    if (root / "requirements.txt").is_file():
        _add_once(report.package_managers, "pip/requirements.txt")
        text = _read_text(root / "requirements.txt").lower()
        for marker, framework in {"django": "Django", "fastapi": "FastAPI", "flask": "Flask", "pytest": "pytest"}.items():
            if marker in text:
                _add_once(report.frameworks if marker != "pytest" else report.test_frameworks, framework)
    for filename, system in {
        "poetry.lock": "Poetry", "Pipfile.lock": "Pipenv", "uv.lock": "uv", "Cargo.lock": "Cargo", "go.sum": "Go modules",
    }.items():
        if (root / filename).is_file():
            _add_once(report.package_managers, system)

    if (root / "Cargo.toml").is_file():
        _add_once(report.package_managers, "Cargo")
        _add_once(report.build_systems, "Cargo")
    if (root / "go.mod").is_file():
        _add_once(report.package_managers, "Go modules")
        _add_once(report.build_systems, "Go")
    if (root / "pom.xml").is_file():
        _add_once(report.package_managers, "Maven")
        _add_once(report.build_systems, "Maven")
    if (root / "build.gradle").is_file() or (root / "build.gradle.kts").is_file():
        _add_once(report.package_managers, "Gradle")
        _add_once(report.build_systems, "Gradle")


def _detect_tooling(root: Path, report: ReconnaissanceReport) -> None:
    workflows = root / ".github" / "workflows"
    if workflows.is_dir():
        _add_once(report.cicd, "GitHub Actions")
    for path, name in [
        (root / ".gitlab-ci.yml", "GitLab CI"), (root / "azure-pipelines.yml", "Azure Pipelines"),
        (root / "Jenkinsfile", "Jenkins"), (root / ".circleci", "CircleCI"),
    ]:
        if path.exists():
            _add_once(report.cicd, name)
    deploy_markers = {
        "vercel.json": "Vercel", "netlify.toml": "Netlify", "fly.toml": "Fly.io", "render.yaml": "Render",
        "Procfile": "Heroku/Procfile", "railway.json": "Railway", "railway.toml": "Railway",
    }
    for filename, target in deploy_markers.items():
        if (root / filename).exists():
            _add_once(report.deployment, target)
    if (root / "docker-compose.yml").is_file() or (root / "docker-compose.yaml").is_file() or (root / "compose.yml").is_file() or (root / "compose.yaml").is_file():
        _add_once(report.deployment, "Docker Compose")
        _add_once(report.build_systems, "Docker Compose")
    if (root / "Dockerfile").is_file() or (root / "Containerfile").is_file():
        _add_once(report.deployment, "Docker")
        _add_once(report.build_systems, "Docker")


def _detect_entry_points(root: Path, files: Iterable[FileEntry]) -> list[str]:
    candidates = []
    exact = {"main.py", "app.py", "server.py", "manage.py", "index.js", "index.ts", "main.js", "main.ts", "server.js", "server.ts", "wsgi.py", "asgi.py"}
    for entry in files:
        if Path(entry.path).name in exact and not entry.is_generated:
            candidates.append(entry.path)
    for entry in files:
        if entry.path.startswith("src/") and Path(entry.path).name in {"main.ts", "main.tsx", "index.ts", "index.tsx", "main.js", "index.js"}:
            if entry.path not in candidates:
                candidates.append(entry.path)
    return sorted(candidates)[:100]


def reconnaissance(root: Path, manifest: AuditManifest) -> ReconnaissanceReport:
    report = ReconnaissanceReport()
    language_counts = Counter(entry.language for entry in manifest.files if entry.language)
    report.languages = {str(k): int(v) for k, v in sorted(language_counts.items())}
    report.configuration_files = sorted(entry.path for entry in manifest.files if entry.is_config)
    report.documentation_files = sorted(entry.path for entry in manifest.files if entry.is_documentation)
    report.source_roots = sorted({entry.path.split("/", 1)[0] for entry in manifest.files if entry.kind == "source"})
    report.likely_entry_points = _detect_entry_points(root, manifest.files)
    _detect_frameworks(root, manifest.files, report)
    _detect_tooling(root, report)
    report.limitations.extend(manifest.limitations)
    return report
