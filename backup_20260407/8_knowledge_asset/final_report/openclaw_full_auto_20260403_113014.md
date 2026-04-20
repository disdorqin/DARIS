# OpenClaw Full Auto Pipeline Report

- Request: rerun_after_repo_map_update2
- Status: success
- Start: 2026-04-03T11:27:04.015814
- End: 2026-04-03T11:30:14.325201

## Round Results
### Round 1
- Literature JSON: 3_literature_workflow\structured_summary\auto_literature_20260403_112824.json
- Reading Summary: 3_literature_workflow\structured_summary\agent_reading_round1.md
- Innovation: 4_research_hypothesis\innovation_round1.md
- Review: 4_research_hypothesis\review_report\innovation_review_round1.md
- Changed files: 5_code_base\optimized\power_models\timesnet_model.py
- Demo metrics: {'MAE': 45.474403381347656, 'RMSE': 64.61547167426312, 'R2': 0.871709406375885}
- Full test log: skipped_by_flag

## Validation Reports
- 8_knowledge_asset/final_report/DARIS_V3_EXECUTION_VALIDATION_20260403_113014.md
- 8_knowledge_asset/final_report/DARIS_V3_EXECUTION_VALIDATION_20260403_113014.json
## Non-Blocking Failures
## Events
- [2026-04-03 11:27:04] 启动前冗余清理 开始 (attempt=1)
- [2026-04-03 11:27:08] 清理完成: 删除 0 项，跳过 0 项
- [2026-04-03 11:27:08] 12标杆项目能力集成 开始 (attempt=1)
- [2026-04-03 11:27:08] 开始集成标杆项目: OpenClaw
- [2026-04-03 11:27:09] 开始集成标杆项目: EvoScientist
- [2026-04-03 11:28:04] 开始集成标杆项目: SciPhi
- [2026-04-03 11:28:06] 开始集成标杆项目: OpenResearch
- [2026-04-03 11:28:07] 开始集成标杆项目: Zotero-GPT
- [2026-04-03 11:28:08] 开始集成标杆项目: PaperAgent
- [2026-04-03 11:28:10] 开始集成标杆项目: AI-Scientist
- [2026-04-03 11:28:11] 开始集成标杆项目: ARIS
- [2026-04-03 11:28:13] 开始集成标杆项目: Aider
- [2026-04-03 11:28:14] 开始集成标杆项目: ML-Agent-Research
- [2026-04-03 11:28:16] 开始集成标杆项目: AutoResearch
- [2026-04-03 11:28:17] 开始集成标杆项目: Zotero
- [2026-04-03 11:28:19] 标杆项目集成完成: 成功/部分=12，非阻断失败=0
- [2026-04-03 11:28:19] 开始执行自动化轮次 1/1
- [2026-04-03 11:28:19] 文献抓取 开始 (attempt=1)
- [2026-04-03 11:28:19] 抓取文献关键词: rerun_after_repo_map_update2
- [2026-04-03 11:28:21] 抓取文献关键词: rerun_after_repo_map_update2 time series forecasting
- [2026-04-03 11:28:23] 抓取文献关键词: rerun_after_repo_map_update2 graph neural network
- [2026-04-03 11:28:24] 文献抓取完成: D:\computer learning\science_workflow\3_literature_workflow\structured_summary\auto_literature_20260403_112824.json
- [2026-04-03 11:28:24] 智能体阅读文献 开始 (attempt=1)
- [2026-04-03 11:28:24] 尝试模型: qwen3.6-plus @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 11:28:25] 模型 qwen3.6-plus 失败: HTTP 400: {"error":{"code":"invalid_parameter_error","message":"model `qwen3.6-plus` is not supported.","param":null,"type":"invalid_request_error"},"request_id":"2b83cce6-08fa-95f0-95fd-2f92934b67f7"}
- [2026-04-03 11:28:25] 尝试模型: qwen3-coder-next @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 11:28:30] 模型 qwen3-coder-next 成功返回。
- [2026-04-03 11:28:30] 提出创新点 开始 (attempt=1)
- [2026-04-03 11:28:30] 尝试模型: qwen3.6-plus @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 11:28:30] 模型 qwen3.6-plus 失败: HTTP 400: {"error":{"code":"invalid_parameter_error","message":"model `qwen3.6-plus` is not supported.","param":null,"type":"invalid_request_error"},"request_id":"c1502547-cd7f-9ea4-b2dc-a1c3bfb2f836"}
- [2026-04-03 11:28:30] 尝试模型: qwen3-coder-next @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 11:28:59] 模型 qwen3-coder-next 成功返回。
- [2026-04-03 11:28:59] 智能体审阅创新点 开始 (attempt=1)
- [2026-04-03 11:28:59] 尝试模型: qwen3.6-plus @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 11:28:59] 模型 qwen3.6-plus 失败: HTTP 400: {"error":{"code":"invalid_parameter_error","message":"model `qwen3.6-plus` is not supported.","param":null,"type":"invalid_request_error"},"request_id":"174e6373-adaa-940d-a531-97d9c1510812"}
- [2026-04-03 11:28:59] 尝试模型: qwen3-coder-next @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 11:29:21] 模型 qwen3-coder-next 成功返回。
- [2026-04-03 11:29:21] 智能体改动代码 开始 (attempt=1)
- [2026-04-03 11:29:21] 自动代码改动完成，涉及文件数: 1
- [2026-04-03 11:29:21] Demo 评估 开始 (attempt=1)
- [2026-04-03 11:30:13] Demo 评估完成: {'MAE': 45.474403381347656, 'RMSE': 64.61547167426312, 'R2': 0.871709406375885}