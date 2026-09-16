# Adding a platform

## 1. Define the boundary

Choose a stable lowercase platform ID and describe the actual output format. Separate platform-specific editorial organization from volatile policy claims.

## 2. Create the skill

Create `skills/platform-write-<id>/SKILL.md` with YAML frontmatter containing exactly one `name` and one discriminating `description`. The `name` must equal the directory name. Add `agents/openai.yaml` with a display name, short description, and default prompt.

The Skill should:

- locate `platform-writing-orchestrator` by frontmatter name;
- reuse the existing fact packet;
- describe platform-specific structure and output fields;
- preserve evidence, qualifications, commercial identity, and required labels;
- return `DEPENDENCY_MISSING` if the common base is unavailable;
- avoid login, upload, publishing, or account operations.

## 3. Register routing

Add one record to `config/platforms.json` and one row to `skills/platform-writing-orchestrator/references/platform-routing.md`. Do not reuse another platform ID.

## 4. Add evidence carefully

Platform policy changes over time. Record current first-party sources, access date, account or content scope, and evidence status. A search snippet or an isolated enforcement screenshot does not prove a complete rule.

## 5. Validate

```bash
python scripts/build_manifest.py
python scripts/validate_repository.py
python -m unittest discover -s tests -v
```

Review the full diff before committing. The manifest should be the last generated file.
