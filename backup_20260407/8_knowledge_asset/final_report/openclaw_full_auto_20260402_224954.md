# OpenClaw Full Auto Pipeline Report

- Request: 今日找电力负荷预测方向文献，自动化流程执行1轮
- Status: failed
- Start: 2026-04-02T22:49:39.432821
- End: 2026-04-02T22:49:54.275433

## Round Results
## Error
智能体阅读文献 最终失败: 全部模型调用失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"e6f0dab6-4c2a-95da-981c-fb76a8ec32c9"}
## Events
- [2026-04-02 22:49:39] 目录归位 开始 (attempt=1)
- [2026-04-02 22:49:39] 目录重构完成，报告: D:\computer learning\science_workflow\8_knowledge_asset\final_report\workspace_reorg_20260402_224939.md
- [2026-04-02 22:49:39] 开始执行自动化轮次 1/1
- [2026-04-02 22:49:39] 文献抓取 开始 (attempt=1)
- [2026-04-02 22:49:39] 抓取文献关键词: 电力负荷预测
- [2026-04-02 22:49:41] 抓取文献关键词: 电力负荷预测 time series forecasting
- [2026-04-02 22:49:43] 抓取文献关键词: 电力负荷预测 graph neural network
- [2026-04-02 22:49:45] 文献抓取完成: D:\computer learning\science_workflow\3_literature_workflow\structured_summary\auto_literature_20260402_224945.json
- [2026-04-02 22:49:45] 智能体阅读文献 开始 (attempt=1)
- [2026-04-02 22:49:45] 尝试模型: qwen3.5-plus
- [2026-04-02 22:49:45] 模型 qwen3.5-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"bcd65b80-1e4f-9d94-9733-70bdc5444b8b"}
- [2026-04-02 22:49:45] 尝试模型: qwen3-coder-next
- [2026-04-02 22:49:45] 模型 qwen3-coder-next 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"5be16af3-1368-993e-adac-65af5d423579"}
- [2026-04-02 22:49:45] 尝试模型: qwen3-max-2026-01-23
- [2026-04-02 22:49:45] 模型 qwen3-max-2026-01-23 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"4d77b57c-994e-9950-a5bc-808211f3caeb"}
- [2026-04-02 22:49:45] 尝试模型: qwen3-coder-plus
- [2026-04-02 22:49:45] 模型 qwen3-coder-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"b7eab33e-4137-9638-b657-0a62012e53bd"}
- [2026-04-02 22:49:45] 尝试模型: kimi-k2.5
- [2026-04-02 22:49:46] 模型 kimi-k2.5 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"dda99ffa-6b3e-90cd-bba8-ed88c880cf04"}
- [2026-04-02 22:49:46] 智能体阅读文献 失败 (attempt=1): 全部模型调用失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"dda99ffa-6b3e-90cd-bba8-ed88c880cf04"}
- [2026-04-02 22:49:48] 智能体阅读文献 开始 (attempt=2)
- [2026-04-02 22:49:48] 尝试模型: qwen3.5-plus
- [2026-04-02 22:49:48] 模型 qwen3.5-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"3f4b30d3-54d3-9ad4-a3e3-5157af524ff2"}
- [2026-04-02 22:49:48] 尝试模型: qwen3-coder-next
- [2026-04-02 22:49:48] 模型 qwen3-coder-next 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"f173cbbd-f70f-95ae-b2cf-67dff4e2c275"}
- [2026-04-02 22:49:48] 尝试模型: qwen3-max-2026-01-23
- [2026-04-02 22:49:48] 模型 qwen3-max-2026-01-23 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"c17a6502-ec9f-9de5-bfb7-15aa1374ea5b"}
- [2026-04-02 22:49:48] 尝试模型: qwen3-coder-plus
- [2026-04-02 22:49:48] 模型 qwen3-coder-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"2c23bb59-125c-97ae-8327-e9b08494798b"}
- [2026-04-02 22:49:48] 尝试模型: kimi-k2.5
- [2026-04-02 22:49:49] 模型 kimi-k2.5 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"e09bc8f3-8c1c-9308-810f-89c3600b9a77"}
- [2026-04-02 22:49:49] 智能体阅读文献 失败 (attempt=2): 全部模型调用失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"e09bc8f3-8c1c-9308-810f-89c3600b9a77"}
- [2026-04-02 22:49:51] 智能体阅读文献 开始 (attempt=3)
- [2026-04-02 22:49:51] 尝试模型: qwen3.5-plus
- [2026-04-02 22:49:51] 模型 qwen3.5-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"808a45c6-8620-951e-b07e-5d342548146a"}
- [2026-04-02 22:49:51] 尝试模型: qwen3-coder-next
- [2026-04-02 22:49:51] 模型 qwen3-coder-next 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"3ae3ed0d-f778-9482-9e7e-be5ea206ca30"}
- [2026-04-02 22:49:51] 尝试模型: qwen3-max-2026-01-23
- [2026-04-02 22:49:51] 模型 qwen3-max-2026-01-23 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"eafb3577-cc45-99b7-ad23-90034ccae4ce"}
- [2026-04-02 22:49:51] 尝试模型: qwen3-coder-plus
- [2026-04-02 22:49:51] 模型 qwen3-coder-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"fef0f057-4e6f-97ca-b823-dec2c7e92ded"}
- [2026-04-02 22:49:51] 尝试模型: kimi-k2.5
- [2026-04-02 22:49:52] 模型 kimi-k2.5 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"e6f0dab6-4c2a-95da-981c-fb76a8ec32c9"}
- [2026-04-02 22:49:52] 智能体阅读文献 失败 (attempt=3): 全部模型调用失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"e6f0dab6-4c2a-95da-981c-fb76a8ec32c9"}
- [2026-04-02 22:49:54] 钉钉告警已发送。