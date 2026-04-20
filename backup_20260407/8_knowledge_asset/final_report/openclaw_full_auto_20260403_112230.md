# OpenClaw Full Auto Pipeline Report

- Request: rerun_github_and_llm
- Status: success
- Start: 2026-04-03T11:19:46.985279
- End: 2026-04-03T11:22:30.746695

## Round Results
### Round 1
- Literature JSON: 3_literature_workflow\structured_summary\auto_literature_20260403_112050.json
- Reading Summary: 3_literature_workflow\structured_summary\agent_reading_round1.md
- Innovation: 4_research_hypothesis\innovation_round1.md
- Review: 4_research_hypothesis\review_report\innovation_review_round1.md
- Changed files: 5_code_base\optimized\power_models\timesnet_model.py
- Demo metrics: {'MAE': 45.474403381347656, 'RMSE': 64.61547167426312, 'R2': 0.871709406375885}
- Full test log: skipped_by_flag

## Validation Reports
- 8_knowledge_asset/final_report/DARIS_V3_EXECUTION_VALIDATION_20260403_112230.md
- 8_knowledge_asset/final_report/DARIS_V3_EXECUTION_VALIDATION_20260403_112230.json
## Non-Blocking Failures
- EvoScientist.clone | attempts=3 | non_blocking=True | error=clone_failed
- SciPhi.core_logic | attempts=3 | non_blocking=True | error=probe_not_found
- PaperAgent.clone | attempts=3 | non_blocking=True | error=clone_failed
- ARIS.clone | attempts=3 | non_blocking=True | error=clone_failed
- AutoResearch.clone | attempts=3 | non_blocking=True | error=clone_failed
## Events
- [2026-04-03 11:19:46] 启动前冗余清理 开始 (attempt=1)
- [2026-04-03 11:19:50] 清理完成: 删除 0 项，跳过 0 项
- [2026-04-03 11:19:50] 12标杆项目能力集成 开始 (attempt=1)
- [2026-04-03 11:19:50] 开始集成标杆项目: OpenClaw
- [2026-04-03 11:19:52] 开始集成标杆项目: EvoScientist
- [2026-04-03 11:20:03] 开始集成标杆项目: SciPhi
- [2026-04-03 11:20:05] 开始集成标杆项目: OpenResearch
- [2026-04-03 11:20:06] 开始集成标杆项目: Zotero-GPT
- [2026-04-03 11:20:08] 开始集成标杆项目: PaperAgent
- [2026-04-03 11:20:18] 开始集成标杆项目: AI-Scientist
- [2026-04-03 11:20:19] 开始集成标杆项目: ARIS
- [2026-04-03 11:20:30] 开始集成标杆项目: Aider
- [2026-04-03 11:20:31] 开始集成标杆项目: ML-Agent-Research
- [2026-04-03 11:20:32] 开始集成标杆项目: AutoResearch
- [2026-04-03 11:20:43] 开始集成标杆项目: Zotero
- [2026-04-03 11:20:44] 标杆项目集成完成: 成功/部分=12，非阻断失败=5
- [2026-04-03 11:20:45] 开始执行自动化轮次 1/1
- [2026-04-03 11:20:45] 文献抓取 开始 (attempt=1)
- [2026-04-03 11:20:45] 抓取文献关键词: rerun_github_and_llm
- [2026-04-03 11:20:46] 抓取文献关键词: rerun_github_and_llm time series forecasting
- [2026-04-03 11:20:48] 抓取文献关键词: rerun_github_and_llm graph neural network
- [2026-04-03 11:20:50] 文献抓取完成: D:\computer learning\science_workflow\3_literature_workflow\structured_summary\auto_literature_20260403_112050.json
- [2026-04-03 11:20:50] 智能体阅读文献 开始 (attempt=1)
- [2026-04-03 11:20:50] 尝试模型: qwen3.6-plus @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 11:20:50] 模型 qwen3.6-plus 失败: HTTP 400: {"error":{"code":"invalid_parameter_error","message":"model `qwen3.6-plus` is not supported.","param":null,"type":"invalid_request_error"},"request_id":"6485fce3-84a6-9c6d-9043-998f71f3767c"}
- [2026-04-03 11:20:50] 尝试模型: qwen3-coder-next @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 11:20:56] 模型 qwen3-coder-next 成功返回。
- [2026-04-03 11:20:56] 提出创新点 开始 (attempt=1)
- [2026-04-03 11:20:56] 尝试模型: qwen3.6-plus @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 11:20:56] 模型 qwen3.6-plus 失败: HTTP 400: {"error":{"code":"invalid_parameter_error","message":"model `qwen3.6-plus` is not supported.","param":null,"type":"invalid_request_error"},"request_id":"b6c7b614-68a8-9fc9-96ca-0683356e5987"}
- [2026-04-03 11:20:56] 尝试模型: qwen3-coder-next @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 11:21:19] 模型 qwen3-coder-next 成功返回。
- [2026-04-03 11:21:19] 智能体审阅创新点 开始 (attempt=1)
- [2026-04-03 11:21:19] 尝试模型: qwen3.6-plus @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 11:21:19] 模型 qwen3.6-plus 失败: HTTP 400: {"error":{"code":"invalid_parameter_error","message":"model `qwen3.6-plus` is not supported.","param":null,"type":"invalid_request_error"},"request_id":"ed4eb591-49ed-990e-9b4f-b922624e7cb9"}
- [2026-04-03 11:21:19] 尝试模型: qwen3-coder-next @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 11:21:33] 模型 qwen3-coder-next 成功返回。
- [2026-04-03 11:21:33] 智能体改动代码 开始 (attempt=1)
- [2026-04-03 11:21:33] 自动代码改动完成，涉及文件数: 1
- [2026-04-03 11:21:33] Demo 评估 开始 (attempt=1)
- [2026-04-03 11:22:30] Demo 评估完成: {'MAE': 45.474403381347656, 'RMSE': 64.61547167426312, 'R2': 0.871709406375885}