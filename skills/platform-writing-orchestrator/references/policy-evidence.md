# 平台规则证据模板

平台规则具有时效性。仓库不把编辑经验写成现行官方规则；执行任务时应查询适用账号、内容格式和地区的一手政策。

每条规则证据至少记录：

- `platform_id`
- `policy_title`
- `official_url`
- `effective_at`（未知可为空）
- `accessed_at`
- `account_or_content_scope`
- `supported_rule`
- `evidence_status`：`VERIFIED` / `PARTIAL` / `ENTRY_ONLY` / `UNVERIFIED`
- `snapshot_or_quote_reference`
- `reviewer_notes`

`PARTIAL` 只支持已读到的具体片段；`ENTRY_ONLY` 只证明入口存在；`UNVERIFIED` 不得转成硬性平台规则。搜索摘要、处罚截图和编辑经验不能单独证明完整规则或唯一触发原因。

法规、平台政策、原创权益、AI 标识、商业合作和账号权限分别核验。缺少证据时可以写草稿，但相关检查必须保持 `UNKNOWN` 或 `REVIEW`。
