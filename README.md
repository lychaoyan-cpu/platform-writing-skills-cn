# Platform Writing Skills CN

Codex / AI Agent skills for evidence-aware Chinese multi-platform writing. One orchestrator normalizes facts, sources, and review boundaries; 16 platform skills then produce platform-specific versions without performing login, upload, or publishing actions.

[中文说明](README.zh-CN.md) · [Architecture](docs/architecture.md) · [Adding a platform](docs/adding-platform.md) · [Security](SECURITY.md)

## What it solves

Reusing one article across every channel often loses factual qualifications, mismatches the format, or turns an editorial check into an unsupported claim about platform approval. This repository separates:

1. fact and evidence preparation in `platform-writing-orchestrator`;
2. platform-specific structure and fields in 16 `platform-write-*` skills;
3. deterministic repository validation for manifests, hashes, declarations, duplicates, local paths, and obvious secrets.

The project does not operate accounts and does not promise approval, recommendation, indexing, or AI citation.

## Scope and verified size

- 17 skills: one orchestrator and 16 platform skills.
- 16 targets: Dayu, WeChat Official Accounts, Zhihu, Xiaohongshu, Toutiao, Baijiahao, Sohu, NetEase, QQ Media, Weibo, Douyin, Kuaishou, WeChat Channels, Bilibili, CSDN, and website knowledge bases.
- The controlled source release was automatically verified as 17 skills and 46 manifest-declared files. Its manifest itself is the 47th on-disk file. The public repository's current file count is maintained separately in `manifest.json`.

## Install

Clone the repository and copy the orchestrator plus the platform skills you need into your Codex skill directory:

```powershell
git clone https://github.com/lychaoyan-cpu/platform-writing-skills-cn.git
Copy-Item -Recurse platform-writing-skills-cn/skills/platform-writing-orchestrator $env:CODEX_HOME/skills/
Copy-Item -Recurse platform-writing-skills-cn/skills/platform-write-zhihu $env:CODEX_HOME/skills/
```

Use your configured skill directory if `CODEX_HOME` is not set, then refresh the skill registry.

## Use with Codex or another agent

Provide a project profile and a traceable fact packet, then name the desired skills:

```text
Use $platform-writing-orchestrator and $platform-write-zhihu.
Follow the field structure in examples/project-profile.example.yaml and my fact packet.
Write a Zhihu answer about evaluating total operating cost for an industrial consumable.
Keep unknown parameters UNKNOWN, add no promotional tail, and do not publish.
```

See `schemas/` for configuration contracts and `examples/` for synthetic inputs. Examples do not represent real companies, customers, prices, test results, or performance.

## Validate the manifest

Only the Python standard library is required:

```bash
python scripts/validate_repository.py
```

After changing tracked files:

```bash
python scripts/build_manifest.py
python scripts/validate_repository.py
```

The validator checks required declarations, skill frontmatter, manifest completeness, SHA-256, duplicate content, disallowed machine-local paths, and high-confidence secret patterns. GitHub Actions runs the same check for pushes and pull requests.

## Validate a fact packet

Fact packets can be checked against `schemas/fact-packet.schema.json` before a writing task starts (standard library only):

```bash
python scripts/validate_fact_packet.py path/to/fact-packet.json
```

With no argument it validates the bundled example. Beyond the schema, it rejects duplicate `fact_id` values within a packet and duplicate `source_id` values within a fact. Regression fixtures for valid and invalid packets live in `tests/fixtures/`.

## Add a platform

Create a `platform-write-<id>` skill, add UI metadata, register it in `config/platforms.json` and the orchestrator routing table, then rebuild and validate the manifest. Do not present editorial preferences as official platform rules. See [docs/adding-platform.md](docs/adding-platform.md).

## Roadmap

- Add behavioral regression fixtures for realistic writing tasks.
- Add optional output-contract validation commands.
- Extend platform field adapters while keeping publishing out of scope.
- Improve security checks while controlling false positives.

Roadmap items are plans, not shipped capabilities.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md); never put credentials or customer data in a public issue.

## License

[MIT](LICENSE)
