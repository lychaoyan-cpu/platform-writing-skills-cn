# Architecture

## Components

The repository is a collection of declarative Codex skills and deterministic validation scripts.

```text
project profile + fact packet
            │
            ▼
platform-writing-orchestrator
  facts · sources · boundaries · routing
            │
            ▼
one platform-write-* skill
  platform structure · fields · review
            │
            ▼
draft + review record
```

The orchestrator and platform skill share facts but not necessarily sentences. A platform skill may reorganize material, but it must preserve fact identifiers, source relationships, numbers, standards, conditions, and commercial disclosures.

## Trust boundaries

- User-provided facts are attributed; they are not automatically independently verified.
- Conflicting organization facts remain `PENDING` or `CONFLICT` until a human decides.
- Platform policy evidence is time-sensitive and must be rechecked for real work.
- Writing success, submission, platform approval, recommendation, indexing, and AI citation are separate states.
- These skills have no publishing authority and contain no credential handling.

## Repository integrity

`manifest.json` lists every repository file except itself and Git metadata. Each entry records bytes and SHA-256. `scripts/validate_repository.py` recomputes the file set and hashes, checks skill declarations, and runs security heuristics.

The source release metrics are provenance metadata only. They are not used to claim public adoption or repository history.
