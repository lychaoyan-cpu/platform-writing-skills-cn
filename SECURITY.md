# Security Policy

## Supported versions

安全修复优先应用于最新发布版本和 `main`。首个支持版本为 `1.0.x`。

## Reporting a vulnerability

请使用 GitHub 仓库的 **Security → Report a vulnerability** 私下报告：

`https://github.com/lychaoyan-cpu/platform-writing-skills-cn/security/advisories/new`

不要在公开 Issue、Discussion 或 Pull Request 中提交 API Key、Token、Cookie、密码、客户资料或可利用细节。报告中请提供受影响版本、复现步骤、影响范围和建议缓解方式；使用占位符替代真实凭据。

维护者会在合理可行的时间内确认报告、评估影响并协调修复与披露。本文件不承诺固定响应时限。

## Repository safeguards

`scripts/validate_repository.py` 会检查常见 Secret 形态、私钥头、本机绝对路径、重复内容和 manifest 哈希。自动扫描不能证明绝对安全，提交者仍需人工审查来源、许可和业务数据。
