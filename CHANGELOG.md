# Changelog

All notable changes to this project will be documented in this file. The format follows Keep a Changelog principles, and releases use Semantic Versioning.

## [Unreleased]

### Planned

- Behavioral regression fixtures for realistic multi-platform writing tasks.
- Optional validation for output contracts.

## [1.1.0] - 2026-10-14

### Added

- `scripts/validate_fact_packet.py`: standard-library-only validation of fact packets against `schemas/fact-packet.schema.json`, plus duplicate `fact_id` / `source_id` integrity checks.
- Regression fixtures under `tests/fixtures/` and seven new unit tests (suite grows from 4 to 11 tests).
- GitHub issue templates (bug report, feature request, platform skill request) and a pull request template aligned with the repository checks.

### Changed

- Repository validator now also requires the v1.1.0 release notes and the fact-packet validator.

## [1.0.0] - 2026-09-16

### Added

- One evidence-aware writing orchestrator and 16 Chinese platform writing skills.
- Generic project-profile and fact-packet schemas with synthetic examples.
- Deterministic manifest generation and repository validation.
- Checks for missing declarations, SKILL frontmatter, duplicate content, local absolute paths, obvious secrets, and SHA-256 consistency.
- GitHub Actions validation workflow and standard OSS governance files.

### Security

- Removed organization-specific names, private business facts, local paths, account context, and internal operational details from the controlled source release.
- Kept publishing, login, credentials, and account operations out of scope.

### Known limitations

- Platform policies change and must be verified from current first-party sources for each real task.
- The skills do not publish, operate accounts, guarantee platform outcomes, or independently verify user-provided facts.
