# Contributing

感谢你改进本项目。提交前请确认变更保持“事实与证据优先、写作与发布分离”的边界。

## 开发流程

1. Fork 仓库并从 `main` 创建主题分支。
2. 只提交与本次变更相关的文件，不加入客户资料、账号信息或凭据。
3. 新增平台时遵循 `docs/adding-platform.md`。
4. 更新文档和示例；示例必须明确为变量或合成数据。
5. 重建并验证清单：

   ```bash
   python scripts/build_manifest.py
   python scripts/validate_repository.py
   python -m unittest discover -s tests -v
   ```

6. 在 Pull Request 中说明变更原因、行为影响、验证结果和已知限制。

## 内容与证据要求

- 不伪造平台规则、采用情况、测试结果或项目指标。
- 时效性平台规则需链接一手来源并记录访问日期与适用范围。
- 不用第三方案例替目标品牌背书。
- 不把编辑 `PASS` 写成平台审核、推荐、索引或引用成功。
- 引入第三方代码或资产前，先确认许可证并记录来源。

## 安全

不要在 Issue、PR、提交历史或测试夹具中放入 Secret、Cookie、账号 ID、客户数据和本机绝对路径。发现漏洞请按 `SECURITY.md` 私下报告。
