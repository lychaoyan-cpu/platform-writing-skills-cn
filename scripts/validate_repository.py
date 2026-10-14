#!/usr/bin/env python3
"""Validate repository declarations, skills, hashes, paths, and obvious secrets."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "manifest.json"
IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "venv", "output", "tmp"}
IGNORED_FILES = {"manifest.json", ".DS_Store", "Thumbs.db"}
REQUIRED_FILES = {
    "README.md",
    "README.zh-CN.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    ".gitignore",
    ".github/workflows/validate.yml",
    "config/platforms.json",
    "config/repository.json",
    "schemas/manifest.schema.json",
    "schemas/project-profile.schema.json",
    "schemas/fact-packet.schema.json",
    "docs/releases/v1.0.0.md",
    "docs/releases/v1.1.0.md",
    "scripts/validate_fact_packet.py",
}
TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".py", ".toml", ".ini", ".cfg", ".svg"}
SKILL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$|^[a-z0-9]$")
WINDOWS_ABSOLUTE_RE = re.compile(r"(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/]|\\\\[^\\\s]+\\[^\\\s]+)")
HOME_ABSOLUTE_RE = re.compile(
    r"(?<![A-Za-z0-9])/" + r"(?:Users|home)/[^/\s]+/|(?<![A-Za-z0-9])/" + "ro" + r"ot/"
)
SECRET_PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "github-token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    "openai-key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "aws-access-key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "google-api-key": re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    "slack-token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "assigned-secret": re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|client[_-]?secret)\b"
        r"\s*[:=]\s*[\"']?(?!\$\{|\{\{|<)[A-Za-z0-9_./+=-]{16,}"
    ),
}


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


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing opening frontmatter delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise ValueError("missing closing frontmatter delimiter") from error
    data: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        key = key.strip()
        if key in data:
            raise ValueError(f"duplicate frontmatter key: {key}")
        data[key] = value.strip().strip('"\'')
    return data, "\n".join(lines[end + 1 :]).strip()


def scan_text(text: str) -> list[str]:
    findings: list[str] = []
    if WINDOWS_ABSOLUTE_RE.search(text):
        findings.append("machine-local Windows/UNC path")
    if HOME_ABSOLUTE_RE.search(text):
        findings.append("machine-local home path")
    for label, pattern in SECRET_PATTERNS.items():
        if pattern.search(text):
            findings.append(f"possible {label}")
    return findings


def load_private_denylist() -> list[str]:
    path_value = os.environ.get("PUBLICATION_DENYLIST_FILE")
    if not path_value:
        return []
    path = Path(path_value)
    if not path.is_file():
        raise ValueError("PUBLICATION_DENYLIST_FILE does not point to a readable file")
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")]


def validate() -> list[str]:
    errors: list[str] = []
    if not MANIFEST_PATH.is_file():
        return ["manifest.json is missing; run scripts/build_manifest.py"]

    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        platforms = json.loads((ROOT / "config" / "platforms.json").read_text(encoding="utf-8"))["platforms"]
        repository = json.loads((ROOT / "config" / "repository.json").read_text(encoding="utf-8"))
    except (json.JSONDecodeError, KeyError) as error:
        return [f"invalid JSON declaration: {error}"]

    actual_files = public_files()
    actual_paths = {path.relative_to(ROOT).as_posix(): path for path in actual_files}
    missing_required = sorted(REQUIRED_FILES - set(actual_paths))
    if missing_required:
        errors.append("missing required files: " + ", ".join(missing_required))

    required_manifest_keys = {"schema_version", "project", "version", "license", "skill_count", "platform_count", "source_release", "skills", "file_count", "files"}
    missing_keys = sorted(required_manifest_keys - set(manifest))
    if missing_keys:
        errors.append("manifest missing keys: " + ", ".join(missing_keys))
        return errors
    if set(manifest) != required_manifest_keys:
        errors.append("manifest has unsupported top-level keys")
    if manifest["schema_version"] != "1.0":
        errors.append("manifest schema_version must be 1.0")
    for key in ("project", "version", "license", "source_release"):
        if manifest[key] != repository[key]:
            errors.append(f"manifest {key} does not match config/repository.json")

    declared = manifest["files"]
    if manifest["file_count"] != len(declared):
        errors.append("manifest file_count does not match files array")
    declared_paths = [item.get("path") for item in declared]
    if len(declared_paths) != len(set(declared_paths)):
        errors.append("manifest contains duplicate file paths")
    if set(declared_paths) != set(actual_paths):
        missing = sorted(set(actual_paths) - set(declared_paths))
        extra = sorted(set(declared_paths) - set(actual_paths))
        if missing:
            errors.append("manifest is missing files: " + ", ".join(missing))
        if extra:
            errors.append("manifest declares absent files: " + ", ".join(extra))
    for item in declared:
        path = actual_paths.get(item.get("path"))
        if path is None:
            continue
        if item.get("bytes") != path.stat().st_size:
            errors.append(f"byte length mismatch: {item['path']}")
        if item.get("sha256") != digest(path):
            errors.append(f"SHA-256 mismatch: {item['path']}")

    skill_directories = sorted(path for path in (ROOT / "skills").iterdir() if path.is_dir())
    skill_names: list[str] = []
    for directory in skill_directories:
        skill_file = directory / "SKILL.md"
        agent_file = directory / "agents" / "openai.yaml"
        if not skill_file.is_file():
            errors.append(f"missing declaration: {skill_file.relative_to(ROOT).as_posix()}")
            continue
        if not agent_file.is_file():
            errors.append(f"missing declaration: {agent_file.relative_to(ROOT).as_posix()}")
        try:
            data, body = parse_frontmatter(skill_file)
        except (UnicodeDecodeError, ValueError) as error:
            errors.append(f"invalid SKILL.md {skill_file.relative_to(ROOT).as_posix()}: {error}")
            continue
        name = data.get("name", "")
        description = data.get("description", "")
        if not SKILL_NAME_RE.fullmatch(name):
            errors.append(f"invalid skill name in {skill_file.relative_to(ROOT).as_posix()}")
        if name != directory.name:
            errors.append(f"skill name does not match directory: {directory.name}")
        if not description or len(description) > 1024:
            errors.append(f"invalid skill description: {directory.name}")
        if not body or "# " not in body:
            errors.append(f"SKILL.md has no meaningful body: {directory.name}")
        skill_names.append(name)
    if len(skill_names) != len(set(skill_names)):
        errors.append("duplicate skill names")

    platform_skills = [item["skill"] for item in platforms]
    if len(platform_skills) != len(set(platform_skills)):
        errors.append("duplicate platform skill mapping")
    missing_platform_skills = sorted(set(platform_skills) - set(skill_names))
    if missing_platform_skills:
        errors.append("platform mappings reference missing skills: " + ", ".join(missing_platform_skills))
    if manifest["skill_count"] != len(skill_names):
        errors.append("manifest skill_count does not match actual skills")
    if manifest["platform_count"] != len(platforms):
        errors.append("manifest platform_count does not match config/platforms.json")
    declared_skill_names = [item.get("name") for item in manifest["skills"]]
    if sorted(declared_skill_names) != sorted(skill_names):
        errors.append("manifest skill list does not match actual skills")

    hashes: dict[str, list[str]] = defaultdict(list)
    denylist: list[str] = []
    try:
        denylist = load_private_denylist()
    except ValueError as error:
        errors.append(str(error))
    for relative, path in actual_paths.items():
        file_hash = digest(path)
        if path.stat().st_size > 0:
            hashes[file_hash].append(relative)
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE", ".gitignore"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"text file is not UTF-8: {relative}")
            continue
        for finding in scan_text(text):
            errors.append(f"{finding}: {relative}")
        for blocked in denylist:
            if blocked.casefold() in text.casefold():
                errors.append(f"private denylist match: {relative}")
                break
    for paths in hashes.values():
        if len(paths) > 1:
            errors.append("duplicate file content: " + ", ".join(sorted(paths)))

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print(f"FAIL: {len(errors)} validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    print(
        "PASS: "
        f"{manifest['skill_count']} skills, "
        f"{manifest['platform_count']} platforms, "
        f"{manifest['file_count']} declared files; "
        "manifest, declarations, format, duplicates, paths, secrets, and hashes verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
