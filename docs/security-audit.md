# Public release security audit

Audit date: 2026-09-16.

## Scope

- Controlled source release `1.0.0`: 47 on-disk files.
- Source manifest: 17 Skills and 46 declared files; the manifest itself is excluded from its own file list.
- Public release: every text file, schema, example, script, workflow, and declaration in this repository.

## Transformations

- Replaced organization, brand, product, account, and internal workflow assumptions with project variables, schemas, or explicitly synthetic examples.
- Renamed all Skill identifiers from the private namespace to `platform-writing-*`.
- Removed copied icon assets because they were identical and unnecessary.
- Replaced a private enforcement case with a synthetic boundary example.
- Replaced dated platform-policy claims with an evidence template that requires current first-party verification.
- Kept credentials, login, upload, publishing, server details, customer information, and production data out of scope.

## Automated checks

The repository validator checks:

- required OSS declarations;
- Skill and UI declaration completeness;
- frontmatter names and descriptions;
- duplicate file content;
- Windows drive paths, UNC paths, and common machine-local home paths;
- high-confidence API token and private-key patterns;
- file-set, byte-length, and SHA-256 consistency.

The source package and the generated public repository were also reviewed for organization-specific identifiers. Candidate matches are not printed by the validator, preventing accidental secret disclosure in CI logs.

The requested public GitHub owner name appears in repository URLs and the MIT copyright notice. It is intentional public metadata and is not treated as a private account identifier.

## Result and limitation

The release is eligible for public hosting only when `python scripts/validate_repository.py` passes on the final commit. Automated scanning reduces risk but cannot prove that no sensitive semantic information exists; maintainers must still review every future contribution.
