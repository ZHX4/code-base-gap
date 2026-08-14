"""Repository source resolution without executing repository content."""
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path


class SourceError(RuntimeError):
    """Raised when a repository source cannot be safely resolved."""


@dataclass(frozen=True)
class ResolvedSource:
    source: str
    requested_ref: str | None
    revision: str
    workspace: Path
    source_kind: str
    repository_metadata: dict[str, object]


def _request_json(url: str, timeout: float = 20.0) -> dict:
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "code-base-gap/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise SourceError(f"GitHub API request failed: {url}: {type(exc).__name__}") from exc
    if not isinstance(data, dict):
        raise SourceError("GitHub API response was not an object")
    return data


def parse_github_source(source: str) -> tuple[str, str]:
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        raise SourceError("only public https://github.com/<owner>/<repo>[.git] sources are supported")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2:
        raise SourceError("GitHub source must identify exactly owner/repository")
    owner, repo = parts
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]+", repo):
        raise SourceError("invalid GitHub repository identifier")
    return owner, repo


def resolve_github(source: str, requested_ref: str | None, destination: Path, max_archive_bytes: int) -> ResolvedSource:
    owner, repo = parse_github_source(source)
    meta = _request_json(f"https://api.github.com/repos/{owner}/{repo}")
    default_branch = str(meta.get("default_branch") or "main")
    ref = requested_ref or default_branch
    ref_info = _request_json(f"https://api.github.com/repos/{owner}/{repo}/commits/{urllib.parse.quote(ref, safe='')}")
    revision = str(ref_info.get("sha") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise SourceError("GitHub did not return a 40-character commit SHA")

    archive_url = f"https://codeload.github.com/{owner}/{repo}/zip/{revision}"
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / "repository.zip"
    try:
        request = urllib.request.Request(archive_url, headers={"User-Agent": "code-base-gap/0.1"})
        with urllib.request.urlopen(request, timeout=60) as response, archive.open("wb") as handle:
            total = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_archive_bytes:
                    raise SourceError(f"archive exceeds configured limit: {max_archive_bytes} bytes")
                handle.write(chunk)
    except SourceError:
        raise
    except Exception as exc:
        raise SourceError(f"repository archive download failed: {type(exc).__name__}") from exc

    workspace = destination / "workspace"
    workspace.mkdir()
    try:
        with zipfile.ZipFile(archive) as zf:
            members = zf.infolist()
            for member in members:
                name = member.filename.replace("\\", "/")
                if not name or name.startswith("/") or ":" in name.split("/")[0] or ".." in Path(name).parts:
                    raise SourceError(f"unsafe archive member: {member.filename}")
                target = (workspace / name).resolve()
                if workspace.resolve() not in target.parents and target != workspace.resolve():
                    raise SourceError(f"archive member escapes workspace: {member.filename}")
            for member in members:
                zf.extract(member, workspace)
    except SourceError:
        shutil.rmtree(workspace, ignore_errors=True)
        raise
    except zipfile.BadZipFile as exc:
        shutil.rmtree(workspace, ignore_errors=True)
        raise SourceError("downloaded repository archive is not a valid ZIP") from exc
    finally:
        archive.unlink(missing_ok=True)

    roots = [path for path in workspace.iterdir() if path.is_dir()]
    if len(roots) == 1:
        actual_root = roots[0]
    else:
        actual_root = workspace
    return ResolvedSource(source, requested_ref, revision, actual_root, "github", meta)


def resolve_local(source: str, destination: Path) -> ResolvedSource:
    root = Path(source).expanduser().resolve()
    if not root.is_dir():
        raise SourceError(f"local source is not a directory: {root}")
    revision = "unversioned"
    metadata: dict[str, object] = {}
    git_dir = root / ".git"
    if git_dir.is_dir():
        try:
            head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
            if head.startswith("ref:"):
                ref = head.split(":", 1)[1].strip()
                ref_file = git_dir / ref
                if ref_file.is_file():
                    revision = ref_file.read_text(encoding="ascii").strip()
                else:
                    packed = git_dir / "packed-refs"
                    if packed.is_file():
                        for line in packed.read_text(encoding="ascii", errors="replace").splitlines():
                            if line and not line.startswith("#") and not line.startswith("^"):
                                sha, name = line.split(" ", 1)
                                if name == ref:
                                    revision = sha
                                    break
            elif re.fullmatch(r"[0-9a-f]{40}", head):
                revision = head
        except OSError:
            metadata["git_revision_read_error"] = True
    return ResolvedSource(source, None, revision, root, "local", metadata)


def resolve_source(source: str, requested_ref: str | None, max_archive_bytes: int) -> tuple[ResolvedSource, tempfile.TemporaryDirectory[str] | None]:
    if source.startswith("https://github.com/"):
        holder = tempfile.TemporaryDirectory(prefix="code-base-gap-phase2-")
        try:
            resolved = resolve_github(source, requested_ref, Path(holder.name), max_archive_bytes)
        except Exception:
            holder.cleanup()
            raise
        return resolved, holder
    return resolve_local(source, Path(tempfile.mkdtemp(prefix="code-base-gap-phase2-local-"))) , None
