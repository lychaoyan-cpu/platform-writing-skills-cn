# Manifest contract

`manifest.json` is generated from repository contents and is not hand-edited.

It records:

- project, version, and license;
- actual Skill and platform counts;
- verified source-release provenance metrics;
- each Skill name, type, path, and platform ID;
- every public repository file except `manifest.json`, with byte length and SHA-256.

Excluding the manifest itself avoids a self-referential hash. Git metadata, Python caches, virtual environments, and local output directories are also excluded.

To update:

```bash
python scripts/build_manifest.py
python scripts/validate_repository.py
```

A clean validation means the current file set and hashes match the manifest. It does not prove legal compliance, correctness of external facts, or absence of every possible secret.
