#!/usr/bin/env python3
"""Build a deterministic SHA-256 manifest for the public repository."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "manifest.json"
IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "venv", "output", "tmp"}
IGNORED_FILES = {"manifest.json", ".DS_Store", "Thumbs.db"}
NAME_RE = re.compile(r"^name:\s*([a-z0-9-]+)\s*$", re.MULTILINE)


def public_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if relative.as_posix() in IGNORED_FILES or path.name in IGNORED_FILES:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def skill_name(skill_file: Path) -> str:
    match = NAME_RE.search(skill_file.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"Missing skill name: {skill_file.relative_to(ROOT)}")
    return match.group(1)


def main() -> int:
    repository = json.loads((ROOT / "config" / "repository.json").read_text(encoding="utf-8"))
    platforms = json.loads((ROOT / "config" / "platforms.json").read_text(encoding="utf-8"))["platforms"]
    platform_by_skill = {item["skill"]: item["id"] for item in platforms}

    skills = []
    for directory in sorted((ROOT / "skills").iterdir(), key=lambda item: item.name):
        if not directory.is_dir():
            continue
        entry = directory / "SKILL.md"
        name = skill_name(entry)
        skills.append(
            {
                "name": name,
                "type": "platform" if name in platform_by_skill else "orchestrator",
                "platform_id": platform_by_skill.get(name),
                "path": directory.relative_to(ROOT).as_posix(),
            }
        )

    files = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in public_files()
    ]

    manifest = {
        "schema_version": "1.0",
        "project": repository["project"],
        "version": repository["version"],
        "license": repository["license"],
        "skill_count": len(skills),
        "platform_count": len(platforms),
        "source_release": repository["source_release"],
        "skills": skills,
        "file_count": len(files),
        "files": files,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {MANIFEST_PATH.name}: {len(skills)} skills, {len(files)} declared files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
