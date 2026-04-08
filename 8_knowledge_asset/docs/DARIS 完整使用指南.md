# DARIS 完整使用指南

## 项目概述

DARIS (Disdorqin Auto Research In Sleep) 是一个自动化科研系统，基于 8 个智能体协同工作，实现从文献检索到实验调优的全流程自动化。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         OpenClaw 全局调度器                              │
│  (openclaw_main.py - 启动入口)                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  2_agent_system/1_research_manager/run.py  (工作流执行器)                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────┬───────────┬───────────┬───────────┬───────────┐
        ▼           ▼           ▼           ▼           ▼           ▼
   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
   │ 环节 1  │  │ 环节 2  │  │ 环节 3  │  │ 环节 4  │  │ 环节 5  │  │ 环节 6  │
   │文献检索 │  │文献阅读 │  │创新提出 │  │创新评审 │  │代码实现 │  │实验调优 │
   └────────┘  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘
        │           │           │           │           │           │
        ▼           ▼           ▼           ▼           ▼           ▼
   kimi-k2.5   kimi-k2.5    glm-5      MiniMax     qwen3.5     qwen3.5
                              (任务调度)  M2.5(评审)  (代码)     (调优)
```

## 启动流程

### 方式一：本地运行（推荐首次使用）

```bash
# 1. 进入项目目录
cd "d:\computer learning\science_workflow"

# 2. 安装依赖
pip install -r openclaw_requirements.txt

# 3. 启动 OpenClaw（不启动钉钉回调）
python openclaw_main.py --no-callback --request "今日找负荷预测方向文献，执行全自动流程一轮" --rounds 1
```

### 方式二：服务器运行（带钉钉回调）

```bash
# 在阿里云服务器上执行
cd /root/DARIS
python openclaw_main.py --daemon --callback-port 8080
```

### 方式三：仅执行工作流（无调度器）

```bash
# 直接调用研究管理器
python 2_agent_system/1_research_manager/run.py --request "执行文献调研" --rounds 1
```

## 完整执行流程

### 阶段 0：启动初始化

```
openclaw_main.py (启动)
    │
    ├── 加载.env 环境变量
    │   ├── 大模型 API 配置（DashScope）
    │   ├── 钉钉配置（可选）
    │   └── 阿里云服务器配置
    │
    ├── 创建 OpenClawScheduler 实例
    │   ├── 初始化 DingTalkBot（消息推送）
    │   ├── 初始化 OpenClawState（状态管理）
    │   └── 启动 DingTalkCallbackServer（回调服务器，可选）
    │
    └── 发送启动通知到钉钉（如果配置了）
```

### 阶段 1：启动前清理

```
_execute_cleanup()
    │
    ├── _workspace_preview() - 全目录预览
    │   ├── 统计目录总数
    │   └── 统计文件总数
    │
    ├── _collect_cleanup_candidates() - 收集清理候选
    │   ├── 缓存目录：__pycache__, .pytest_cache, .mypy_cache, .ruff_cache
    │   ├── Office 锁文件：~$*.docx, ~$*.xlsx
    │   └── 临时文件：*.tmp, *.temp, *.bak, *.log(超过 2 天)
    │
    ├── _execute_cleanup() - 执行清理
    │   ├── 删除缓存目录
    │   └── 删除临时文件
    │
    └── 生成清理报告
        ├── 7_monitor_system/system_log/cleanup_report_*.json
        └── 7_monitor_system/system_log/cleanup_report_*.md
```

### 阶段 2：标杆项目集成

```
_integrate_benchmark_projects()
    │
    ├── 加载标杆项目配置 (1_config/base/benchmark_projects.json)
    │   └── 12 个开源项目：
    │       ├── OpenResearch, PaperAgent, AI-Scientist, ARIS
    │       ├── Aider, ML-Agent-Research, AutoResearch
    │       └── EvoScientist, SciPhi, Zotero, Zotero-GPT, OpenClaw
    │
    ├── 对每个项目执行：
    │   ├── _clone_or_update_repo() - 克隆/更新仓库
    │   │   ├── 尝试 HTTPS 克隆（3 次重试）
    │   │   ├── 失败后切换 SSH
    │   │   └── 再失败使用 Gitee 镜像
    │   │
    │   ├── _validate_probe_files() - 验证探针文件
    │   │   └── 检查 README.md 等关键文件是否存在
    │   │
    │   ├── _write_integration_adapter() - 生成适配文档
    │   │   └── 2_agent_system/integration/*_adapter.md
    │   │
    │   └── _validate_project_usability() - 可用性验证
    │       └── 执行 git rev-parse --short HEAD
    │
    └── 生成集成报告
        ├── 8_knowledge_asset/final_report/benchmark_integration_*.json
        └── 8_knowledge_asset/final_report/benchmark_integration_*.md
```

### 阶段 3：执行工作流轮次

```
for round_id in range(1, rounds + 1):
    execute_round(round_id)
```

#### 步骤 3.1：文献抓取

```
_crawl_literature(keywords, limit=8)
    │
    ├── 提取关键词（从请求中）
    │   └── 例："负荷预测" → ["负荷预测", "负荷预测 time series", "负荷预测 forecasting"]
    │
    ├── 调用 CrossRef API
    │   └── https://api.crossref.org/works?query={keyword}&rows=8
    │
    ├── 解析响应
    │   ├── 标题
    │   ├── 作者
    │   ├── DOI
    │   ├── 年份
    │   └── 摘要
    │
    └── 保存文献列表
        └── 3_literature_workflow/literature_asset/crawled/auto_literature_*.json
```

#### 步骤 3.2：文献阅读与总结

```
_call_llm_with_fallback(system_prompt, user_prompt)
    │
    ├── 获取可用 API 端点
    │   ├── 北京：https://dashscope.aliyuncs.com/compatible-mode/v1
    │   ├── 新加坡：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    │   └── 美国：https://dashscope-us.aliyuncs.com/compatible-mode/v1
    │
    ├── 获取模型候选列表
    │   └── ["qwen3.5-plus", "qwen3-max", "kimi-k2.5", ...]
    │
    ├── 轮询调用（直到成功）
    │   └── POST {base_url}/chat/completions
    │       ├── model: kimi-k2.5（文献阅读指定模型）
    │       ├── temperature: 0.2
    │       └── messages: [system_prompt, user_prompt]
    │
    ├── 如果全部失败 → _local_stage_fallback() 本地兜底
    │
    └── 保存总结
        └── 3_literature_workflow/structured_summary/agent_reading_round*.md
```

**Prompt 示例**：
```python
system_prompt = "你是 DARIS 文献调研智能体，请只输出结构化中文结论。"

user_prompt = f"""
任务：阅读以下文献条目并总结研究脉络、常见缺陷、可利用空白。

{literature_text}
"""
```

#### 步骤 3.3：创新点生成

```
_call_llm_with_fallback(...)
    │
    ├── 使用模型：glm-5（创新点提出指定模型）
    │
    ├── system_prompt = "你是 DARIS 创新挖掘智能体，请提出 3 个可执行创新点..."
    │
    ├── user_prompt = f"""
    基于文献阅读结论提出创新点，要求适配 MTGNN/TimesNet/XGBoost。
    
    {summary_text}
    """
    │
    └── 保存创新点
        └── 4_research_hypothesis/innovation_round*.md
```

#### 步骤 3.4：创新点评审

```
_call_llm_with_fallback(...)
    │
    ├── 使用模型：MiniMax-M2.5（创新点评审指定模型）
    │
    ├── system_prompt = "你是 DARIS 质量评审智能体..."
    │
    ├── user_prompt = f"""
    请评审以下创新方案，输出：通过项、风险项、必须修改项。
    
    {innovation_text}
    """
    │
    └── 保存评审报告
        └── 4_research_hypothesis/review_report/innovation_review_round*.md
```

#### 步骤 3.5：代码改动

```
_apply_code_edits()
    │
    ├── 定义规则替换（硬编码的改动点）
    │   ├── xgboost_model.py:
    │   │   ├── n_estimators: 140 → 160
    │   │   └── max_depth: 5 → 6
    │   │
    │   ├── timesnet_model.py:
    │   │   ├── epochs: 8 → 10
    │   │   └── lambda_phy: 0.1 → 0.12
    │   │
    │   └── mtgnn_model.py:
    │       ├── hidden_dim: 80 → 88
    │       └── epochs: 8 → 10
    │
    ├── 执行替换
    │   └── 字符串替换（如果匹配则替换）
    │
    └── 提交 Git
        └── git add + git commit
```

#### 步骤 3.6：Demo 评估

```
_run_demo()
    │
    ├── 加载数据 (6_experiment_execution/data/shandong_pmos_hourly.csv)
    │
    ├── 导入模型 (5_code_base/optimized/power_models/)
    │
    ├── 执行 XGBoost 训练
    │
    └── 保存指标
        └── 6_experiment_execution/experiment_result/auto_demo_metrics.json
```

#### 步骤 3.7：全量测试（可选）

```
_run_full_baselines()
    │
    ├── 执行脚本：6_experiment_execution/pipeline/run_round_fixed_pipeline.py
    │
    ├── 训练三个基线模型：
    │   ├── MTGNN
    │   ├── TimesNet
    │   └── XGBoost
    │
    └── 保存日志
        └── 6_experiment_execution/tuning_log/auto_full_pipeline_stdout.log
```

### 阶段 4：生成报告

```
_write_execution_validation_report(final_result)
    │
    ├── 生成 JSON 报告
    │   └── 8_knowledge_asset/final_report/openclaw_full_auto_*.json
    │
    ├── 生成 Markdown 报告
    │   └── 8_knowledge_asset/final_report/openclaw_full_auto_*.md
    │
    └── 提交 Git
        └── git add + git commit
```

### 阶段 5：Skills 沉淀

```
_append_deep_retrospective(round_id, summary)
    │
    ├── 分析本轮瓶颈
    │
    ├── 分析根本原因
    │
    ├── 提出优化方向
    │
    └── 更新 skills_library.md
        └── 8_knowledge_asset/iteration_memory/skills_library.md
```

## 目录结构

```
DARIS/
├── openclaw_main.py                      # 【启动入口】OpenClaw 全局调度
├── openclaw_requirements.txt             # 依赖清单
├── .env                                  # 环境配置
│
├── 2_agent_system/
│   ├── base_agent.py                     # 智能体基类
│   ├── dingtalk_callback.py              # 钉钉回调服务器
│   └── 1_research_manager/
│       ├── run.py                        # 【工作流执行器】
│       └── workspace_reorganizer.py      # 目录重构工具
│
├── 3_literature_workflow/
│   ├── literature_asset/crawled/         # 抓取的文献
│   └── structured_summary/               # 结构化总结
│
├── 4_research_hypothesis/
│   ├── innovation_round*.md              # 创新点提案
│   └── review_report/                    # 评审报告
│
├── 5_code_base/
│   ├── baseline/                         # 基线模型
│   └── optimized/                        # 优化模型
│
├── 6_experiment_execution/
│   ├── data/                             # 实验数据
│   ├── experiment_result/                # 实验结果
│   ├── pipeline/                         # 执行脚本
│   └── tuning_log/                       # 调优日志
│
├── 7_monitor_system/
│   ├── system_log/                       # 系统日志
│   └── dingtalk_log/                     # 钉钉消息日志
│
└── 8_knowledge_asset/
    ├── iteration_memory/
    │   └── skills_library.md             # 技能知识库
    └── final_report/                     # 最终报告
```

## 关键配置文件

### .env

```bash
# 大模型 API 配置
DASHSCOPE_API_KEY=sk-xxxxxxxx
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 模型路由
LITERATURE_MODEL=kimi-k2.5
INNOVATION_MODEL=glm-5
INNOVATION_REVIEW_MODEL=MiniMax-M2.5
CODE_IMPLEMENTATION_MODEL=qwen3.5-plus

# 钉钉配置（可选）
WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxx
```

### 1_config/base/benchmark_projects.json

定义 12 个标杆项目的仓库地址和验证规则。

## 常见问题

### Q1: 如何跳过某些阶段？

```bash
# 跳过标杆项目集成
python openclaw_main.py --skip-benchmark

# 跳过全量测试
python openclaw_main.py --skip-full-baseline
```

### Q2: 如何查看执行日志？

```bash
# 查看最新工作流日志
cat 7_monitor_system/system_log/openclaw_workflow_*.log

# 查看清理报告
cat 8_knowledge_asset/final_report/cleanup_report_*.md
```

### Q3: 如何回滚到上一版本？

```bash
git reset --hard HEAD~1
```

### Q4: 大模型调用失败怎么办？

系统会自动 fallback：
1. 尝试下一个 API 端点
2. 尝试下一个模型
3. 使用本地兜底生成

## 相关文档

- [钉钉回调配置指南](./钉钉回调配置指南.md)
- [服务器部署指南](./SERVER_DEPLOY.md)
- [项目架构与执行说明](./项目架构与执行说明.md)