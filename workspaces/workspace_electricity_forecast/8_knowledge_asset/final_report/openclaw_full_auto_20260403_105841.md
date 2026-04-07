# OpenClaw Full Auto Pipeline Report

- Request: daris_v3_full_run
- Status: success
- Start: 2026-04-03T10:38:44.451679
- End: 2026-04-03T10:58:41.206657

## Round Results
### Round 1
- Literature JSON: 3_literature_workflow\structured_summary\auto_literature_20260403_105232.json
- Reading Summary: 3_literature_workflow\structured_summary\agent_reading_round1.md
- Innovation: 4_research_hypothesis\innovation_round1.md
- Review: 4_research_hypothesis\review_report\innovation_review_round1.md
- Changed files: 5_code_base\optimized\power_models\timesnet_model.py
- Demo metrics: {'MAE': 45.474403381347656, 'RMSE': 64.61547167426312, 'R2': 0.871709406375885}
- Full test log: 6_experiment_execution\tuning_log\auto_full_pipeline_stdout.log

## Validation Reports
- 8_knowledge_asset/final_report/DARIS_V3_EXECUTION_VALIDATION_20260403_105841.md
- 8_knowledge_asset/final_report/DARIS_V3_EXECUTION_VALIDATION_20260403_105841.json
## Non-Blocking Failures
- OpenClaw.clone | attempts=3 | non_blocking=True | error=clone_failed
- EvoScientist.clone | attempts=3 | non_blocking=True | error=clone_failed
- SciPhi.core_logic | attempts=3 | non_blocking=True | error=probe_not_found
- PaperAgent.clone | attempts=3 | non_blocking=True | error=clone_failed
- ARIS.clone | attempts=3 | non_blocking=True | error=clone_failed
- Aider.clone | attempts=3 | non_blocking=True | error=clone_failed
- ML-Agent-Research.clone | attempts=3 | non_blocking=True | error=clone_failed
- AutoResearch.clone | attempts=3 | non_blocking=True | error=clone_failed
- Zotero.clone | attempts=3 | non_blocking=True | error=clone_failed
## Events
- [2026-04-03 10:38:44] 启动前冗余清理 开始 (attempt=1)
- [2026-04-03 10:38:47] 清理完成: 删除 3 项，跳过 0 项
- [2026-04-03 10:38:47] 12标杆项目能力集成 开始 (attempt=1)
- [2026-04-03 10:38:47] 开始集成标杆项目: OpenClaw
- [2026-04-03 10:40:10] 开始集成标杆项目: EvoScientist
- [2026-04-03 10:42:00] 开始集成标杆项目: SciPhi
- [2026-04-03 10:42:01] 开始集成标杆项目: OpenResearch
- [2026-04-03 10:42:02] 开始集成标杆项目: Zotero-GPT
- [2026-04-03 10:42:43] 开始集成标杆项目: PaperAgent
- [2026-04-03 10:44:53] 开始集成标杆项目: AI-Scientist
- [2026-04-03 10:45:49] 开始集成标杆项目: ARIS
- [2026-04-03 10:47:35] 开始集成标杆项目: Aider
- [2026-04-03 10:48:42] 开始集成标杆项目: ML-Agent-Research
- [2026-04-03 10:49:49] 开始集成标杆项目: AutoResearch
- [2026-04-03 10:51:19] 开始集成标杆项目: Zotero
- [2026-04-03 10:52:25] 标杆项目集成完成: 成功/部分=12，非阻断失败=9
- [2026-04-03 10:52:26] 目录归位 开始 (attempt=1)
- [2026-04-03 10:52:26] 目录重构完成，报告: D:\computer learning\science_workflow\8_knowledge_asset\final_report\workspace_reorg_20260403_105226.md
- [2026-04-03 10:52:26] 开始执行自动化轮次 1/1
- [2026-04-03 10:52:26] 文献抓取 开始 (attempt=1)
- [2026-04-03 10:52:26] 抓取文献关键词: daris_v3_full_run
- [2026-04-03 10:52:28] 抓取文献关键词: daris_v3_full_run time series forecasting
- [2026-04-03 10:52:30] 抓取文献关键词: daris_v3_full_run graph neural network
- [2026-04-03 10:52:32] 文献抓取完成: D:\computer learning\science_workflow\3_literature_workflow\structured_summary\auto_literature_20260403_105232.json
- [2026-04-03 10:52:32] 智能体阅读文献 开始 (attempt=1)
- [2026-04-03 10:52:32] 尝试模型: qwen3.5-plus
- [2026-04-03 10:52:32] 模型 qwen3.5-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"8754dd1b-e0b2-99b2-88bc-473e6f8b3716"}
- [2026-04-03 10:52:32] 尝试模型: qwen3-coder-next
- [2026-04-03 10:52:32] 模型 qwen3-coder-next 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"e6e253d2-180f-9692-8571-1ce436989878"}
- [2026-04-03 10:52:32] 尝试模型: qwen3-max-2026-01-23
- [2026-04-03 10:52:33] 模型 qwen3-max-2026-01-23 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"ae268f19-0046-912d-b80c-390d6fbdbbe6"}
- [2026-04-03 10:52:33] 尝试模型: qwen3-coder-plus
- [2026-04-03 10:52:33] 模型 qwen3-coder-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"b2a9c435-3d13-962c-b9cb-fd591ff47e47"}
- [2026-04-03 10:52:33] 尝试模型: kimi-k2.5
- [2026-04-03 10:52:33] 模型 kimi-k2.5 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"63193b35-6d6f-931a-905d-c6a88cc3392c"}
- [2026-04-03 10:52:33] 全部模型调用失败，切换本地兜底生成。最近错误: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"63193b35-6d6f-931a-905d-c6a88cc3392c"}
- [2026-04-03 10:52:33] 提出创新点 开始 (attempt=1)
- [2026-04-03 10:52:33] 尝试模型: qwen3.5-plus
- [2026-04-03 10:52:33] 模型 qwen3.5-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"dd766174-3f7b-93b8-9190-c7d0b35cb093"}
- [2026-04-03 10:52:33] 尝试模型: qwen3-coder-next
- [2026-04-03 10:52:33] 模型 qwen3-coder-next 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"58bbee5b-20a2-9b40-a756-e6fcfca2f3ea"}
- [2026-04-03 10:52:33] 尝试模型: qwen3-max-2026-01-23
- [2026-04-03 10:52:33] 模型 qwen3-max-2026-01-23 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"1ef105ef-e69b-9fc7-a979-79055e4f63fe"}
- [2026-04-03 10:52:33] 尝试模型: qwen3-coder-plus
- [2026-04-03 10:52:34] 模型 qwen3-coder-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"1c080566-6fe7-9bfb-9c0e-37599b572e17"}
- [2026-04-03 10:52:34] 尝试模型: kimi-k2.5
- [2026-04-03 10:52:34] 模型 kimi-k2.5 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"b6bf4691-8f3f-9e46-96ba-d33b44c9d93c"}
- [2026-04-03 10:52:34] 全部模型调用失败，切换本地兜底生成。最近错误: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"b6bf4691-8f3f-9e46-96ba-d33b44c9d93c"}
- [2026-04-03 10:52:34] 智能体审阅创新点 开始 (attempt=1)
- [2026-04-03 10:52:34] 尝试模型: qwen3.5-plus
- [2026-04-03 10:52:34] 模型 qwen3.5-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"453fbe58-d450-90e5-9438-e10552229944"}
- [2026-04-03 10:52:34] 尝试模型: qwen3-coder-next
- [2026-04-03 10:52:34] 模型 qwen3-coder-next 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"4873731c-76de-98bd-a489-f461bba7d183"}
- [2026-04-03 10:52:34] 尝试模型: qwen3-max-2026-01-23
- [2026-04-03 10:52:34] 模型 qwen3-max-2026-01-23 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"ced5e230-956f-9ddf-8e59-7117bde5fb7e"}
- [2026-04-03 10:52:34] 尝试模型: qwen3-coder-plus
- [2026-04-03 10:52:35] 模型 qwen3-coder-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"f4fdb451-0d10-9581-a86e-4bfe0b862db8"}
- [2026-04-03 10:52:35] 尝试模型: kimi-k2.5
- [2026-04-03 10:52:35] 模型 kimi-k2.5 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"c6af6f7b-d67d-90a1-a63e-9cb525d11164"}
- [2026-04-03 10:52:35] 全部模型调用失败，切换本地兜底生成。最近错误: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"c6af6f7b-d67d-90a1-a63e-9cb525d11164"}
- [2026-04-03 10:52:35] 智能体改动代码 开始 (attempt=1)
- [2026-04-03 10:52:35] 自动代码改动完成，涉及文件数: 1
- [2026-04-03 10:52:35] Demo 评估 开始 (attempt=1)
- [2026-04-03 10:53:20] Demo 评估完成: {'MAE': 45.474403381347656, 'RMSE': 64.61547167426312, 'R2': 0.871709406375885}
- [2026-04-03 10:53:20] 三基线改动测试 开始 (attempt=1)
- [2026-04-03 10:53:20] 执行三基线+优化测试脚本: D:\computer learning\science_workflow\6_experiment_execution\pipeline\run_round_fixed_pipeline.py
- [2026-04-03 10:58:41] 全量测试完成，日志: D:\computer learning\science_workflow\6_experiment_execution\tuning_log\auto_full_pipeline_stdout.log
- [2026-04-03 10:58:41] Git add 失败: The following paths are ignored by one of your .gitignore files:
6_experiment_execution/tuning_log/auto_full_pipeline_stdout.log
hint: Use -f if you really want to add them.
hint: Disable this message