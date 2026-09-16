# 输出契约

## 人工交稿

交付标题、正文、必要图注与来源，并附简短编辑说明。公开正文不得混入 JSON、内部风险列表或执行日志。用户指定 DOCX、HTML 等格式时，应真正生成相应格式，不得只修改扩展名。

## 程序记录

字段可以为空，但不得伪造已执行状态：

- `article_id`、`platform_id`、`format`、`account_context`
- `fact_packet_id`、`fact_ids_used`
- `source_records[]`：`title`、`url`、`published_at`、`accessed_at`、`supported_claims`、`evidence_status`
- `title`、`summary`、`body`、`optional_faq`、`cards_or_script`、`media_requirements`
- `brand_mentions[]`：`text`、`role`、`evidence_id`、`reader_value`、`commercial_relationship`
- `ai_creation_mode`、`originality_status`、`commercial_disclosure`
- `rule_version`、`rule_evidence_status`、`skill_name`、`skill_version`、`writer_model`
- `source_draft_hash`、`final_content_hash`
- `checks[]`：`scope`、`result`、`evidence`、`reason`
- `decision`：`READY_FOR_REVIEW` / `PASS` / `REWRITE` / `REVIEW` / `BLOCK`
- `content_stage`：`DRAFT` / `ADAPTED` / `EDITOR_CHECKED`
- `runtime_integration_verified: false`，除非真实运行证据证明已接入
- `published: false`，写作 Skill 无发布权限

未知事实不进入正文。未执行的检查写 `UNKNOWN`，不以模型评分替代。缺规则、缺素材或缺授权时，当前稿件进入 `REVIEW`，其他稿件不受影响。

重复度检查需要目标平台的历史正文或指纹库；没有数据时写 `UNKNOWN`。版式变化不能消除语义重复。

## 集成约定

1. 读取所在仓库的治理说明和事实源，不把安装说明当生产事实。
2. 注册平台 ID 到 Skill frontmatter 名称的映射，按名称解析依赖。
3. 总编只生成一次事实包；平台 Skill 只生成自己的平台版本。
4. 保存规则版本、Skill 版本、输入与输出哈希。事实或正文改变后，旧审批失效。
5. 不擅自改变发布授权、调度或账号状态；失败只隔离对应稿件。
6. 测试至少覆盖正常知识稿、有证据案例、无证据性能稿和多平台重组。
7. 分开记录提交回执、平台审核、推荐、索引和 AI 引用，不从一个结果推导另一个结果。
