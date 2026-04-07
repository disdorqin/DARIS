# OpenClaw Full Auto Pipeline Report

- Request: rerun_github_and_llm_bg
- Status: success
- Start: 2026-04-03T11:22:09.480157
- End: 2026-04-03T11:24:44.437099

## Round Results
### Round 1
- Literature JSON: 3_literature_workflow\structured_summary\auto_literature_20260403_112312.json
- Reading Summary: 3_literature_workflow\structured_summary\agent_reading_round1.md
- Innovation: 4_research_hypothesis\innovation_round1.md
- Review: 4_research_hypothesis\review_report\innovation_review_round1.md
- Changed files: 5_code_base\optimized\power_models\timesnet_model.py
- Demo metrics: {'MAE': 45.474403381347656, 'RMSE': 64.61547167426312, 'R2': 0.871709406375885}
- Full test log: skipped_by_flag

## Validation Reports
- 8_knowledge_asset/final_report/DARIS_V3_EXECUTION_VALIDATION_20260403_112444.md
- 8_knowledge_asset/final_report/DARIS_V3_EXECUTION_VALIDATION_20260403_112444.json
## Non-Blocking Failures
- EvoScientist.clone | attempts=3 | non_blocking=True | error=clone_failed
- SciPhi.core_logic | attempts=3 | non_blocking=True | error=probe_not_found
- PaperAgent.clone | attempts=3 | non_blocking=True | error=clone_failed
- ARIS.clone | attempts=3 | non_blocking=True | error=clone_failed
- AutoResearch.clone | attempts=3 | non_blocking=True | error=clone_failed
## Events
- [2026-04-03 11:22:09] 启动前冗余清理 开始 (attempt=1)
- [2026-04-03 11:22:15] 清理完成: 删除 1 项，跳过 0 项
- [2026-04-03 11:22:15] 12标杆项目能力集成 开始 (attempt=1)
- [2026-04-03 11:22:15] 开始集成标杆项目: OpenClaw
- [2026-04-03 11:22:17] 开始集成标杆项目: EvoScientist
- [2026-04-03 11:22:28] 开始集成标杆项目: SciPhi
- [2026-04-03 11:22:29] 开始集成标杆项目: OpenResearch
- [2026-04-03 11:22:30] 开始集成标杆项目: Zotero-GPT
- [2026-04-03 11:22:32] 开始集成标杆项目: PaperAgent
- [2026-04-03 11:22:42] 开始集成标杆项目: AI-Scientist
- [2026-04-03 11:22:43] 开始集成标杆项目: ARIS
- [2026-04-03 11:22:53] 开始集成标杆项目: Aider
- [2026-04-03 11:22:54] 开始集成标杆项目: ML-Agent-Research
- [2026-04-03 11:22:56] 开始集成标杆项目: AutoResearch
- [2026-04-03 11:23:05] 开始集成标杆项目: Zotero
- [2026-04-03 11:23:07] 标杆项目集成完成: 成功/部分=12，非阻断失败=5
- [2026-04-03 11:23:07] 开始执行自动化轮次 1/1
- [2026-04-03 11:23:07] 文献抓取 开始 (attempt=1)
- [2026-04-03 11:23:07] 抓取文献关键词: rerun_github_and_llm_bg
- [2026-04-03 11:23:09] 抓取文献关键词: rerun_github_and_llm_bg time series forecasting
- [2026-04-03 11:23:11] 抓取文献关键词: rerun_github_and_llm_bg graph neural network
- [2026-04-03 11:23:12] 文献抓取完成: D:\computer learning\science_workflow\3_literature_workflow\structured_summary\auto_literature_20260403_112312.json
- [2026-04-03 11:23:12] 智能体阅读文献 开始 (attempt=1)
- [2026-04-03 11:23:12] 尝试模型: qwen3.6-plus @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 11:23:13] 模型 qwen3.6-plus 失败: HTTP 400: {"error":{"code":"invalid_parameter_error","message":"model `qwen3.6-plus` is not supported.","param":null,"type":"invalid_request_error"},"request_id":"02897168-4943-9651-a14f-4525a43a67f7"}
- [2026-04-03 11:23:13] 尝试模型: qwen3-coder-next @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 11:23:20] 模型 qwen3-coder-next 成功返回。
- [2026-04-03 11:23:20] 提出创新点 开始 (attempt=1)
- [2026-04-03 11:23:20] 尝试模型: qwen3.6-plus @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 11:23:21] 模型 qwen3.6-plus 失败: HTTP 400: {"error":{"code":"invalid_parameter_error","message":"model `qwen3.6-plus` is not supported.","param":null,"type":"invalid_request_error"},"request_id":"6731707d-415c-93f6-bc84-6dc566fe62db"}
- [2026-04-03 11:23:21] 尝试模型: qwen3-coder-next @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 11:23:39] 模型 qwen3-coder-next 成功返回。
- [2026-04-03 11:23:39] 智能体审阅创新点 开始 (attempt=1)
- [2026-04-03 11:23:39] 尝试模型: qwen3.6-plus @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 11:23:39] 模型 qwen3.6-plus 失败: HTTP 400: {"error":{"code":"invalid_parameter_error","message":"model `qwen3.6-plus` is not supported.","param":null,"type":"invalid_request_error"},"request_id":"61414b4a-b3f3-9190-a616-43108cfe71e1"}
- [2026-04-03 11:23:39] 尝试模型: qwen3-coder-next @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 11:23:50] 模型 qwen3-coder-next 成功返回。
- [2026-04-03 11:23:50] 智能体改动代码 开始 (attempt=1)
- [2026-04-03 11:23:50] 自动代码改动完成，涉及文件数: 1
- [2026-04-03 11:23:50] Demo 评估 开始 (attempt=1)
- [2026-04-03 11:24:44] Demo 评估完成: {'MAE': 45.474403381347656, 'RMSE': 64.61547167426312, 'R2': 0.871709406375885}