# OpenClaw Full Auto Pipeline Report

- Request: 今日找电力负荷预测方向文献，自动化流程执行1轮
- Status: failed
- Start: 2026-04-02T22:48:13.265908
- End: 2026-04-02T22:48:28.668684

## Round Results
## Error
智能体阅读文献 最终失败: 全部模型调用失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"b02e047c-ca07-98df-ae99-d211d0990216"}
## Events
- [2026-04-02 22:48:13] 目录归位 开始 (attempt=1)
- [2026-04-02 22:48:13] 目录重构完成，报告: D:\computer learning\science_workflow\8_knowledge_asset\final_report\workspace_reorg_20260402_224813.md
- [2026-04-02 22:48:13] 开始执行自动化轮次 1/1
- [2026-04-02 22:48:13] 文献抓取 开始 (attempt=1)
- [2026-04-02 22:48:13] 抓取文献关键词: 电力负荷预测
- [2026-04-02 22:48:16] 抓取文献关键词: 电力负荷预测 time series forecasting
- [2026-04-02 22:48:18] 抓取文献关键词: 电力负荷预测 graph neural network
- [2026-04-02 22:48:19] 文献抓取完成: D:\computer learning\science_workflow\3_literature_workflow\structured_summary\auto_literature_20260402_224819.json
- [2026-04-02 22:48:19] 智能体阅读文献 开始 (attempt=1)
- [2026-04-02 22:48:19] 尝试模型: qwen3.5-plus
- [2026-04-02 22:48:20] 模型 qwen3.5-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"1645cc48-1ff3-9b36-ba13-bedf2f0d80a4"}
- [2026-04-02 22:48:20] 尝试模型: qwen3-coder-next
- [2026-04-02 22:48:20] 模型 qwen3-coder-next 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"774d6dc7-54ac-9ae6-a41a-f8163c4a3705"}
- [2026-04-02 22:48:20] 尝试模型: qwen3-max-2026-01-23
- [2026-04-02 22:48:20] 模型 qwen3-max-2026-01-23 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"3eef1034-17a2-9586-8200-08100e745e96"}
- [2026-04-02 22:48:20] 尝试模型: qwen3-coder-plus
- [2026-04-02 22:48:20] 模型 qwen3-coder-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"804bf51a-bdac-9701-9583-4efc6306d95c"}
- [2026-04-02 22:48:20] 尝试模型: kimi-k2.5
- [2026-04-02 22:48:20] 模型 kimi-k2.5 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"46fadfa7-9a6e-9810-96cf-187bcc97492f"}
- [2026-04-02 22:48:20] 智能体阅读文献 失败 (attempt=1): 全部模型调用失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"46fadfa7-9a6e-9810-96cf-187bcc97492f"}
- [2026-04-02 22:48:22] 智能体阅读文献 开始 (attempt=2)
- [2026-04-02 22:48:22] 尝试模型: qwen3.5-plus
- [2026-04-02 22:48:22] 模型 qwen3.5-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"a570ad4d-1a20-9a99-a57d-2857c54e6a80"}
- [2026-04-02 22:48:22] 尝试模型: qwen3-coder-next
- [2026-04-02 22:48:23] 模型 qwen3-coder-next 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"ce6ae49f-f1a7-9301-ae75-1ef36ad7b830"}
- [2026-04-02 22:48:23] 尝试模型: qwen3-max-2026-01-23
- [2026-04-02 22:48:23] 模型 qwen3-max-2026-01-23 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"a008607c-ce25-9bd5-9e00-30e59c615e25"}
- [2026-04-02 22:48:23] 尝试模型: qwen3-coder-plus
- [2026-04-02 22:48:23] 模型 qwen3-coder-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"0af75985-e9a0-9302-b020-35093441cd8d"}
- [2026-04-02 22:48:23] 尝试模型: kimi-k2.5
- [2026-04-02 22:48:23] 模型 kimi-k2.5 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"bfc8c8af-031c-9da6-a9b2-2f05c3c7a37b"}
- [2026-04-02 22:48:23] 智能体阅读文献 失败 (attempt=2): 全部模型调用失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"bfc8c8af-031c-9da6-a9b2-2f05c3c7a37b"}
- [2026-04-02 22:48:25] 智能体阅读文献 开始 (attempt=3)
- [2026-04-02 22:48:25] 尝试模型: qwen3.5-plus
- [2026-04-02 22:48:25] 模型 qwen3.5-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"2f9ebd22-fa1f-96bc-aeae-fe0b295d74f3"}
- [2026-04-02 22:48:25] 尝试模型: qwen3-coder-next
- [2026-04-02 22:48:25] 模型 qwen3-coder-next 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"ab639fe7-d563-9c44-8e81-c7178d7d4083"}
- [2026-04-02 22:48:25] 尝试模型: qwen3-max-2026-01-23
- [2026-04-02 22:48:26] 模型 qwen3-max-2026-01-23 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"179972be-530b-921f-af51-55e4b3049083"}
- [2026-04-02 22:48:26] 尝试模型: qwen3-coder-plus
- [2026-04-02 22:48:26] 模型 qwen3-coder-plus 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"d46b4a5d-601d-90b6-99d3-56f4c735c0bc"}
- [2026-04-02 22:48:26] 尝试模型: kimi-k2.5
- [2026-04-02 22:48:26] 模型 kimi-k2.5 失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"b02e047c-ca07-98df-ae99-d211d0990216"}
- [2026-04-02 22:48:26] 智能体阅读文献 失败 (attempt=3): 全部模型调用失败: HTTP 401: {"error":{"message":"Incorrect API key provided. For details, see: https://help.aliyun.com/zh/model-studio/error-code#apikey-error","type":"invalid_request_error","param":null,"code":"invalid_api_key"},"request_id":"b02e047c-ca07-98df-ae99-d211d0990216"}
- [2026-04-02 22:48:28] 钉钉告警已发送。