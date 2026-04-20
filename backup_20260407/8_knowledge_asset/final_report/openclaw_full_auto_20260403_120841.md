# OpenClaw Full Auto Pipeline Report

- Request: 严格按照DARIS_v3md文档执行
- Status: success
- Start: 2026-04-03T12:02:34.824518
- End: 2026-04-03T12:08:41.642887

## Round Results
### Round 1
- Literature JSON: 3_literature_workflow\structured_summary\auto_literature_20260403_120311.json
- Reading Summary: 3_literature_workflow\structured_summary\agent_reading_round1.md
- Innovation: 4_research_hypothesis\innovation_round1.md
- Review: 4_research_hypothesis\review_report\innovation_review_round1.md
- Changed files: 5_code_base\optimized\power_models\timesnet_model.py
- Demo metrics: {'MAE': 45.474403381347656, 'RMSE': 64.61547167426312, 'R2': 0.871709406375885}
- Full test log: 6_experiment_execution\tuning_log\auto_full_pipeline_stdout.log

## Validation Reports
- 8_knowledge_asset/final_report/DARIS_V3_EXECUTION_VALIDATION_20260403_120841.md
- 8_knowledge_asset/final_report/DARIS_V3_EXECUTION_VALIDATION_20260403_120841.json
## Non-Blocking Failures
## Events
- [2026-04-03 12:02:34] 启动前冗余清理 开始 (attempt=1)
- [2026-04-03 12:02:38] 清理完成: 删除 2 项，跳过 0 项
- [2026-04-03 12:02:38] 12标杆项目能力集成 开始 (attempt=1)
- [2026-04-03 12:02:38] 开始集成标杆项目: OpenClaw
- [2026-04-03 12:02:40] 开始集成标杆项目: EvoScientist
- [2026-04-03 12:02:42] 开始集成标杆项目: SciPhi
- [2026-04-03 12:02:44] 开始集成标杆项目: OpenResearch
- [2026-04-03 12:02:45] 开始集成标杆项目: Zotero-GPT
- [2026-04-03 12:02:51] 开始集成标杆项目: PaperAgent
- [2026-04-03 12:02:53] 开始集成标杆项目: AI-Scientist
- [2026-04-03 12:02:54] 开始集成标杆项目: ARIS
- [2026-04-03 12:02:56] 开始集成标杆项目: Aider
- [2026-04-03 12:02:58] 开始集成标杆项目: ML-Agent-Research
- [2026-04-03 12:02:59] 开始集成标杆项目: AutoResearch
- [2026-04-03 12:03:01] 开始集成标杆项目: Zotero
- [2026-04-03 12:03:04] 标杆项目集成完成: 成功/部分=12，非阻断失败=0
- [2026-04-03 12:03:04] 目录归位 开始 (attempt=1)
- [2026-04-03 12:03:04] 目录重构完成，报告: D:\computer learning\science_workflow\8_knowledge_asset\final_report\workspace_reorg_20260403_120304.md
- [2026-04-03 12:03:04] 开始执行自动化轮次 1/1
- [2026-04-03 12:03:04] 文献抓取 开始 (attempt=1)
- [2026-04-03 12:03:04] 抓取文献关键词: 严格按照DARIS_v3md文档执行
- [2026-04-03 12:03:07] 抓取文献关键词: 严格按照DARIS_v3md文档执行 time series forecasting
- [2026-04-03 12:03:09] 抓取文献关键词: 严格按照DARIS_v3md文档执行 graph neural network
- [2026-04-03 12:03:11] 文献抓取完成: D:\computer learning\science_workflow\3_literature_workflow\structured_summary\auto_literature_20260403_120311.json
- [2026-04-03 12:03:11] 智能体阅读文献 开始 (attempt=1)
- [2026-04-03 12:03:11] 尝试模型: qwen3.6-plus @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 12:03:12] 模型 qwen3.6-plus 失败: HTTP 400: {"error":{"code":"invalid_parameter_error","message":"model `qwen3.6-plus` is not supported.","param":null,"type":"invalid_request_error"},"request_id":"f010b156-09f3-9439-b90b-d47820ade379"}
- [2026-04-03 12:03:12] 尝试模型: qwen3-coder-next @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 12:03:17] 模型 qwen3-coder-next 成功返回。
- [2026-04-03 12:03:17] 提出创新点 开始 (attempt=1)
- [2026-04-03 12:03:17] 尝试模型: qwen3.6-plus @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 12:03:18] 模型 qwen3.6-plus 失败: HTTP 400: {"error":{"code":"invalid_parameter_error","message":"model `qwen3.6-plus` is not supported.","param":null,"type":"invalid_request_error"},"request_id":"f51eeef2-86fa-9bb4-a1f7-ab61eeca593f"}
- [2026-04-03 12:03:18] 尝试模型: qwen3-coder-next @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 12:03:39] 模型 qwen3-coder-next 成功返回。
- [2026-04-03 12:03:39] 智能体审阅创新点 开始 (attempt=1)
- [2026-04-03 12:03:39] 尝试模型: qwen3.6-plus @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 12:03:41] 模型 qwen3.6-plus 失败: HTTP 400: {"error":{"code":"invalid_parameter_error","message":"model `qwen3.6-plus` is not supported.","param":null,"type":"invalid_request_error"},"request_id":"bd209c88-a4ab-9132-aad7-2597909c6b47"}
- [2026-04-03 12:03:41] 尝试模型: qwen3-coder-next @ https://coding.dashscope.aliyuncs.com/v1
- [2026-04-03 12:03:56] 模型 qwen3-coder-next 成功返回。
- [2026-04-03 12:03:56] 智能体改动代码 开始 (attempt=1)
- [2026-04-03 12:03:56] 自动代码改动完成，涉及文件数: 1
- [2026-04-03 12:03:56] Demo 评估 开始 (attempt=1)
- [2026-04-03 12:04:38] Demo 评估完成: {'MAE': 45.474403381347656, 'RMSE': 64.61547167426312, 'R2': 0.871709406375885}
- [2026-04-03 12:04:38] 三基线改动测试 开始 (attempt=1)
- [2026-04-03 12:04:38] 执行三基线+优化测试脚本: D:\computer learning\science_workflow\6_experiment_execution\pipeline\run_round_fixed_pipeline.py
- [2026-04-03 12:08:41] 全量测试完成，日志: D:\computer learning\science_workflow\6_experiment_execution\tuning_log\auto_full_pipeline_stdout.log
- [2026-04-03 12:08:41] Git add 失败: The following paths are ignored by one of your .gitignore files:
6_experiment_execution/tuning_log/auto_full_pipeline_stdout.log
hint: Use -f if you really want to add them.
hint: Disable this message