# OpenClaw Full Auto Pipeline Report

- Request: 今日找电力负荷预测方向文献，自动化流程执行1轮
- Status: success
- Start: 2026-04-02T22:52:56.628452
- End: 2026-04-02T23:01:41.308386

## Round Results
### Round 1
- Literature JSON: 3_literature_workflow\structured_summary\auto_literature_20260402_225302.json
- Reading Summary: 3_literature_workflow\structured_summary\agent_reading_round1.md
- Innovation: 4_research_hypothesis\innovation_round1.md
- Review: 4_research_hypothesis\review_report\innovation_review_round1.md
- Changed files: 5_code_base\optimized\power_models\xgboost_model.py, 5_code_base\optimized\power_models\timesnet_model.py, 5_code_base\optimized\power_models\mtgnn_model.py
- Demo metrics: {'MAE': 45.474403381347656, 'RMSE': 64.61547167426312, 'R2': 0.871709406375885}
- Full test log: 6_experiment_execution\tuning_log\auto_full_pipeline_stdout.log

## Events
- [2026-04-02 22:52:56] 目录归位 开始 (attempt=1)
- [2026-04-02 22:52:56] 目录重构完成，报告: D:\computer learning\science_workflow\8_knowledge_asset\final_report\workspace_reorg_20260402_225256.md
- [2026-04-02 22:52:56] 开始执行自动化轮次 1/1
- [2026-04-02 22:52:56] 文献抓取 开始 (attempt=1)
- [2026-04-02 22:52:56] 抓取文献关键词: 电力负荷预测
- [2026-04-02 22:52:58] 抓取文献关键词: 电力负荷预测 time series forecasting
- [2026-04-02 22:53:00] 抓取文献关键词: 电力负荷预测 graph neural network
- [2026-04-02 22:53:02] 文献抓取完成: D:\computer learning\science_workflow\3_literature_workflow\structured_summary\auto_literature_20260402_225302.json
- [2026-04-02 22:53:02] 智能体阅读文献 开始 (attempt=1)
- [2026-04-02 22:53:02] 尝试模型: qwen3.5-plus
- [2026-04-02 22:53:03] 模型 qwen3.5-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"df074838-8a33-994b-b5d7-9792540d48d6"}
- [2026-04-02 22:53:03] 尝试模型: qwen3-coder-next
- [2026-04-02 22:53:03] 模型 qwen3-coder-next 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"ec5f53a9-a3a2-9997-96a2-14116c42e77f"}
- [2026-04-02 22:53:03] 尝试模型: qwen3-max-2026-01-23
- [2026-04-02 22:53:03] 模型 qwen3-max-2026-01-23 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"354516df-f28d-979a-ad91-f6ecf861fdac"}
- [2026-04-02 22:53:03] 尝试模型: qwen3-coder-plus
- [2026-04-02 22:53:03] 模型 qwen3-coder-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"3432e443-9541-918e-a1ec-ee215a592e84"}
- [2026-04-02 22:53:03] 尝试模型: kimi-k2.5
- [2026-04-02 22:53:03] 模型 kimi-k2.5 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"e6d1d724-414e-91ae-b4bc-ea9ad61d546d"}
- [2026-04-02 22:53:03] 全部模型调用失败，切换本地兜底生成。最近错误: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"e6d1d724-414e-91ae-b4bc-ea9ad61d546d"}
- [2026-04-02 22:53:03] 提出创新点 开始 (attempt=1)
- [2026-04-02 22:53:03] 尝试模型: qwen3.5-plus
- [2026-04-02 22:53:03] 模型 qwen3.5-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"36d6bf67-8925-9ace-8b32-1d3ab7908495"}
- [2026-04-02 22:53:03] 尝试模型: qwen3-coder-next
- [2026-04-02 22:53:03] 模型 qwen3-coder-next 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"a2bb2be6-4828-9974-8fc9-3323fab2e4ee"}
- [2026-04-02 22:53:03] 尝试模型: qwen3-max-2026-01-23
- [2026-04-02 22:53:04] 模型 qwen3-max-2026-01-23 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"48251fc1-6d53-9961-a4bf-9a7dd89ebaac"}
- [2026-04-02 22:53:04] 尝试模型: qwen3-coder-plus
- [2026-04-02 22:53:04] 模型 qwen3-coder-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"aa327a06-1583-90d1-a7ca-c76ba804472f"}
- [2026-04-02 22:53:04] 尝试模型: kimi-k2.5
- [2026-04-02 22:53:04] 模型 kimi-k2.5 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"9fa4d281-cae2-9b1d-8a1b-1385562aa6e2"}
- [2026-04-02 22:53:04] 全部模型调用失败，切换本地兜底生成。最近错误: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"9fa4d281-cae2-9b1d-8a1b-1385562aa6e2"}
- [2026-04-02 22:53:04] 智能体审阅创新点 开始 (attempt=1)
- [2026-04-02 22:53:04] 尝试模型: qwen3.5-plus
- [2026-04-02 22:53:04] 模型 qwen3.5-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"d5b50691-c54d-98ba-9361-e19ec4f11555"}
- [2026-04-02 22:53:04] 尝试模型: qwen3-coder-next
- [2026-04-02 22:53:05] 模型 qwen3-coder-next 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"c3302f27-fb99-98db-b93a-98088e8141c7"}
- [2026-04-02 22:53:05] 尝试模型: qwen3-max-2026-01-23
- [2026-04-02 22:53:05] 模型 qwen3-max-2026-01-23 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"92977533-245c-9a98-b8c7-1001ac75103b"}
- [2026-04-02 22:53:05] 尝试模型: qwen3-coder-plus
- [2026-04-02 22:53:05] 模型 qwen3-coder-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"1436ed46-05d4-91a9-bc96-8b75e4001543"}
- [2026-04-02 22:53:05] 尝试模型: kimi-k2.5
- [2026-04-02 22:53:05] 模型 kimi-k2.5 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"2edbfc54-720a-9989-a332-b5aadb1ceca6"}
- [2026-04-02 22:53:05] 全部模型调用失败，切换本地兜底生成。最近错误: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"2edbfc54-720a-9989-a332-b5aadb1ceca6"}
- [2026-04-02 22:53:05] 智能体改动代码 开始 (attempt=1)
- [2026-04-02 22:53:05] 自动代码改动完成，涉及文件数: 3
- [2026-04-02 22:53:05] Demo 评估 开始 (attempt=1)
- [2026-04-02 22:54:24] Demo 评估完成: {'MAE': 45.474403381347656, 'RMSE': 64.61547167426312, 'R2': 0.871709406375885}
- [2026-04-02 22:54:24] 三基线改动测试 开始 (attempt=1)
- [2026-04-02 22:54:24] 执行三基线+优化测试脚本: D:\computer learning\science_workflow\6_experiment_execution\pipeline\run_round_fixed_pipeline.py
- [2026-04-02 23:01:41] 全量测试完成，日志: D:\computer learning\science_workflow\6_experiment_execution\tuning_log\auto_full_pipeline_stdout.log