# Platform Writing Skills CN

一组面向中文内容工作的 Codex / AI Agent Skills：用一个总编 Skill 统一事实、证据和审查边界，再由 16 个平台 Skill 生成适合目标平台的独立版本。

[English](README.md) · [架构](docs/architecture.md) · [扩展平台](docs/adding-platform.md) · [安全说明](SECURITY.md)

## 解决什么问题

同一份资料直接复制到不同平台，通常会造成体裁不匹配、事实限定丢失、品牌表达失真，或把编辑检查误写成平台审核结果。本项目把工作拆成三层：

1. 总编建立事实包、来源记录和公共边界。
2. 目标平台 Skill 只负责该平台的结构、语气与字段。
3. 校验器检查 Skill、声明文件、清单、重复内容、本机绝对路径、明显 Secret 与 SHA-256。

写作与发布分离。本项目不登录账号、不上传、不发布，也不保证审核、推荐、索引或 AI 引用。

## 项目规模

- 17 个 Skill：1 个总编 + 16 个平台 Skill。
- 支持 16 个目标入口：大鱼号、微信公众号、知乎、小红书、头条号、百家号、搜狐号、网易号、企鹅号、微博、抖音、快手、视频号、哔哩哔哩、CSDN、官网知识库。
- 私有源版本 `1.0.0` 经自动核验为 17 个 Skill、46 个清单声明文件；源目录另有清单自身，因此磁盘文件总数为 47。公开仓库的当前文件数由 `manifest.json` 自动维护，不与源包口径混用。

## Skill 架构

```text
platform-writing-orchestrator
├── editorial-core        事实、证据、体裁和品牌边界
├── output-contract       人工交稿与程序记录约定
├── platform-routing      平台 ID → Skill 名称
└── policy-evidence       时效性平台规则证据模板
        │
        ├── platform-write-wechat
        ├── platform-write-zhihu
        ├── platform-write-douyin
        └── ... 共 16 个平台 Skill
```

平台 Skill 按 frontmatter 的 `name` 解析，不依赖安装目录名。总编只建立一次事实包；平台 Skill 不递归调用总编生成第二份母稿。

## 安装

克隆仓库后，把 `skills/` 下需要的目录复制到 Codex 可发现的 Skill 目录。平台 Skill 依赖总编公共参考，建议安装总编和所需平台 Skill：

```powershell
git clone https://github.com/lychaoyan-cpu/platform-writing-skills-cn.git
Copy-Item -Recurse platform-writing-skills-cn/skills/platform-writing-orchestrator $env:CODEX_HOME/skills/
Copy-Item -Recurse platform-writing-skills-cn/skills/platform-write-zhihu $env:CODEX_HOME/skills/
```

如果未设置 `CODEX_HOME`，请使用你的 Codex 配置所指定的 Skill 目录。复制后重新启动或刷新 Skill 注册表。

## 在 Codex / AI Agent 中使用

先提供项目配置和可追溯事实，再点名目标 Skill。例如：

```text
使用 $platform-writing-orchestrator 和 $platform-write-zhihu。
读取 examples/project-profile.example.yaml 的字段结构和我的事实包，
将“如何评估一种工业耗材的总使用成本”写成知乎回答。
未知参数保持 UNKNOWN，不添加品牌尾段，不执行发布。
```

单平台任务也可以直接调用对应 Skill。没有共同底座时，平台 Skill 会标记 `DEPENDENCY_MISSING`，不得冒充完整审查。

## 配置、Schema 与示例

- `schemas/project-profile.schema.json`：组织、品牌、禁用表达和内容边界。
- `schemas/fact-packet.schema.json`：断言、来源、证据等级和公开状态。
- `schemas/manifest.schema.json`：仓库清单结构。
- `examples/project-profile.example.yaml`：只含变量的配置模板。
- `examples/fact-packet.example.json`：明确标记为合成数据的事实包。
- `examples/request.example.md`：可复制的 Agent 请求。

示例不代表真实企业、客户、价格、性能或检测结果。

## manifest 校验

仓库只使用 Python 标准库：

```bash
python scripts/validate_repository.py
```

校验内容包括：

- `manifest.json` 与 Schema 要求；
- 17 个 Skill、`SKILL.md` 和 `agents/openai.yaml` 的完整性；
- YAML frontmatter 的 `name` / `description` 基础格式；
- 清单中的文件集合、大小和 SHA-256；
- 重复文件内容；
- Windows、macOS、Linux 用户目录等非法绝对路径；
- 常见高置信 Secret 形态和私钥头；
- 仓库必需声明文件。

修改文件后先重建清单，再校验：

```bash
python scripts/build_manifest.py
python scripts/validate_repository.py
```

GitHub Actions 会在 push 和 pull request 时执行相同检查。

## 事实包校验

写作任务开始前，可用仓库自带脚本按 `schemas/fact-packet.schema.json` 校验事实包（只用 Python 标准库）：

```bash
python scripts/validate_fact_packet.py path/to/fact-packet.json
```

不带参数时校验自带示例。除 Schema 本身外，还会拒绝同一事实包内重复的 `fact_id` 和同一条事实内重复的 `source_id`。有效与无效事实包的回归夹具在 `tests/fixtures/`。

## 扩展新平台

1. 从现有平台 Skill 的结构开始，但重新写平台特有组织方式。
2. 使用新的 `platform-write-<id>` 名称，并补 `agents/openai.yaml`。
3. 更新 `config/platforms.json` 与总编路由表。
4. 不把未经核验的编辑经验写成官方平台规则。
5. 重建 manifest 并运行校验。

完整说明见 [docs/adding-platform.md](docs/adding-platform.md)。

## Roadmap

- 增加面向真实任务的行为回归夹具，而不是只匹配固定措辞。
- 提供可选的输出契约 JSON 校验命令。
- 增加更多平台字段适配，同时保持写作与发布分离。
- 持续更新安全规则并减少误报。

Roadmap 是维护计划，不代表功能已经交付。

## 贡献

欢迎提交可复现的问题、平台策略改进、Schema 和校验规则。请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。安全问题请按 [SECURITY.md](SECURITY.md) 私下报告，不要在公开 Issue 中提交 Secret 或客户资料。

## License

[MIT](LICENSE)
