# OpenClaw Full Auto Pipeline Report

- Request: debug_run_3
- Status: success
- Start: 2026-04-03T10:31:30.121599
- End: 2026-04-03T10:37:55.545086

## Round Results
### Round 1
- Literature JSON: 3_literature_workflow\structured_summary\auto_literature_20260403_103704.json
- Reading Summary: 3_literature_workflow\structured_summary\agent_reading_round1.md
- Innovation: 4_research_hypothesis\innovation_round1.md
- Review: 4_research_hypothesis\review_report\innovation_review_round1.md
- Changed files: 5_code_base\optimized\power_models\timesnet_model.py
- Demo metrics: {'MAE': 45.474403381347656, 'RMSE': 64.61547167426312, 'R2': 0.871709406375885}
- Full test log: skipped_by_flag

## Validation Reports
- 8_knowledge_asset/final_report/DARIS_V3_EXECUTION_VALIDATION_20260403_103755.md
- 8_knowledge_asset/final_report/DARIS_V3_EXECUTION_VALIDATION_20260403_103755.json
## Non-Blocking Failures
- EvoScientist.clone | attempts=3 | non_blocking=True | error=clone_failed
- SciPhi.core_logic | attempts=3 | non_blocking=True | error=probe_not_found
- PaperAgent.clone | attempts=3 | non_blocking=True | error=clone_failed
- ARIS.clone | attempts=3 | non_blocking=True | error=clone_failed
- AutoResearch.clone | attempts=3 | non_blocking=True | error=clone_failed
## Events
- [2026-04-03 10:31:30] 启动前冗余清理 开始 (attempt=1)
- [2026-04-03 10:31:32] 清理完成: 删除 0 项，跳过 0 项
- [2026-04-03 10:31:32] 12标杆项目能力集成 开始 (attempt=1)
- [2026-04-03 10:31:32] 开始集成标杆项目: OpenClaw
- [2026-04-03 10:31:33] 开始集成标杆项目: EvoScientist
- [2026-04-03 10:31:43] 开始集成标杆项目: SciPhi
- [2026-04-03 10:31:44] 开始集成标杆项目: OpenResearch
- [2026-04-03 10:31:45] 开始集成标杆项目: Zotero-GPT
- [2026-04-03 10:31:47] 开始集成标杆项目: PaperAgent
- [2026-04-03 10:31:58] 开始集成标杆项目: AI-Scientist
- [2026-04-03 10:33:06] 开始集成标杆项目: ARIS
- [2026-04-03 10:33:16] 开始集成标杆项目: Aider
- [2026-04-03 10:34:19] 开始集成标杆项目: ML-Agent-Research
- [2026-04-03 10:34:23] 开始集成标杆项目: AutoResearch
- [2026-04-03 10:34:33] 开始集成标杆项目: Zotero
- [2026-04-03 10:36:52] 标杆项目集成完成: 成功/部分=12，非阻断失败=5
- [2026-04-03 10:36:52] 开始执行自动化轮次 1/1
- [2026-04-03 10:36:52] 文献抓取 开始 (attempt=1)
- [2026-04-03 10:36:52] 抓取文献关键词: debug_run_3
- [2026-04-03 10:36:59] 抓取文献关键词: debug_run_3 time series forecasting
- [2026-04-03 10:37:02] 抓取文献关键词: debug_run_3 graph neural network
- [2026-04-03 10:37:04] 文献抓取完成: D:\computer learning\science_workflow\3_literature_workflow\structured_summary\auto_literature_20260403_103704.json
- [2026-04-03 10:37:04] 智能体阅读文献 开始 (attempt=1)
- [2026-04-03 10:37:04] 尝试模型: qwen3.5-plus
- [2026-04-03 10:37:04] 模型 qwen3.5-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"e8094176-c40d-95e0-8e34-ca003f4cddf8"}
- [2026-04-03 10:37:04] 尝试模型: qwen3-coder-next
- [2026-04-03 10:37:04] 模型 qwen3-coder-next 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"cc01777f-29c7-9f16-91c4-d79691f516e6"}
- [2026-04-03 10:37:04] 尝试模型: qwen3-max-2026-01-23
- [2026-04-03 10:37:05] 模型 qwen3-max-2026-01-23 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"e5f92d3d-f908-9694-aab2-9161fe600d23"}
- [2026-04-03 10:37:05] 尝试模型: qwen3-coder-plus
- [2026-04-03 10:37:05] 模型 qwen3-coder-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"4fe7c41e-696c-9b62-b1c5-2e0b507da6ab"}
- [2026-04-03 10:37:05] 尝试模型: kimi-k2.5
- [2026-04-03 10:37:05] 模型 kimi-k2.5 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"8fe96c88-836e-9e4f-9b5d-a853eb57945c"}
- [2026-04-03 10:37:05] 全部模型调用失败，切换本地兜底生成。最近错误: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"8fe96c88-836e-9e4f-9b5d-a853eb57945c"}
- [2026-04-03 10:37:05] 提出创新点 开始 (attempt=1)
- [2026-04-03 10:37:05] 尝试模型: qwen3.5-plus
- [2026-04-03 10:37:05] 模型 qwen3.5-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"4a15c4e4-6776-956c-9173-77fed8ccdff8"}
- [2026-04-03 10:37:05] 尝试模型: qwen3-coder-next
- [2026-04-03 10:37:05] 模型 qwen3-coder-next 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"5aeef5de-be55-9e6b-a21a-893d16f0a0cf"}
- [2026-04-03 10:37:05] 尝试模型: qwen3-max-2026-01-23
- [2026-04-03 10:37:06] 模型 qwen3-max-2026-01-23 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"deccd256-73ed-958f-8a35-211945627c91"}
- [2026-04-03 10:37:06] 尝试模型: qwen3-coder-plus
- [2026-04-03 10:37:06] 模型 qwen3-coder-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"47b42d06-ec22-918d-b6c3-91ae30ce357a"}
- [2026-04-03 10:37:06] 尝试模型: kimi-k2.5
- [2026-04-03 10:37:06] 模型 kimi-k2.5 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"fc17682f-1779-9329-9a08-813d397978be"}
- [2026-04-03 10:37:06] 全部模型调用失败，切换本地兜底生成。最近错误: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"fc17682f-1779-9329-9a08-813d397978be"}
- [2026-04-03 10:37:06] 智能体审阅创新点 开始 (attempt=1)
- [2026-04-03 10:37:06] 尝试模型: qwen3.5-plus
- [2026-04-03 10:37:06] 模型 qwen3.5-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"b9441fe2-1290-9362-b542-c49e39a815c7"}
- [2026-04-03 10:37:06] 尝试模型: qwen3-coder-next
- [2026-04-03 10:37:06] 模型 qwen3-coder-next 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"c59ef5e7-d21e-93d5-9562-8e8b081494bc"}
- [2026-04-03 10:37:06] 尝试模型: qwen3-max-2026-01-23
- [2026-04-03 10:37:06] 模型 qwen3-max-2026-01-23 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"37fc86b6-f1ec-9c54-8cba-2f42c8babc21"}
- [2026-04-03 10:37:06] 尝试模型: qwen3-coder-plus
- [2026-04-03 10:37:07] 模型 qwen3-coder-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"b7781f75-31a7-9ba6-9086-380d145ed46f"}
- [2026-04-03 10:37:07] 尝试模型: kimi-k2.5
- [2026-04-03 10:37:07] 模型 kimi-k2.5 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"31d4dca2-d6d6-9869-956d-e11dce407e52"}
- [2026-04-03 10:37:07] 全部模型调用失败，切换本地兜底生成。最近错误: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"31d4dca2-d6d6-9869-956d-e11dce407e52"}
- [2026-04-03 10:37:07] 智能体改动代码 开始 (attempt=1)
- [2026-04-03 10:37:07] 自动代码改动完成，涉及文件数: 1
- [2026-04-03 10:37:07] Demo 评估 开始 (attempt=1)
- [2026-04-03 10:37:55] Demo 评估完成: {'MAE': 45.474403381347656, 'RMSE': 64.61547167426312, 'R2': 0.871709406375885}