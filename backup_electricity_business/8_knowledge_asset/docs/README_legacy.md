# DARIS 全自动化科研闭环工作流

**版本号**：v3.0  
**适配模型**：MTGNN / TimesNet / XGBoost  
**核心特性**：全链路闭环、无人值守迭代、工具 100% 适配、隐私隔离

---

## 核心特性

- **三模型专属闭环**：深度适配 MTGNN/TimesNet/XGBoost，从文献到调优全流程定制
- **全链路无断层**：六智能体分工明确，输入输出标准化，Cline 可逐步骤执行
- **隐私安全隔离**：.env 独立管理密钥，隐私数据不进 Git，阿里云传输加密
- **无人值守迭代**：ARIS+AutoResearch 双引擎，自动调优、回滚、回溯，7*24 运行
- **科研资产沉淀**：Obsidian+Git 双同步，记忆库迭代优化，避免重复踩坑

---

## 目录结构

```
DARIS/
├── .env                      # 隐私配置（不进 Git）
├── .env.example              # 配置模板
├── .gitignore                # Git 忽略规则
├── README.md                 # 项目说明
├── research_definition.md    # 研究问题定义
├── config/
│   ├── prompts/              # Prompt 模板目录
│   ├── search_rules.yaml     # 文献检索规则
│   ├── zotero_sync.yaml      # Zotero 同步规则
│   ├── data_feature.yaml     # 数据特征定义
│   ├── innovation_prompt.md  # 创新点挖掘模板
│   ├── program.md            # AutoResearch 调优规则
│   ├── agent_config.yaml     # 智能体分工配置
│   ├── cost_config.yaml      # 成本预算配置
│   ├── fuse_config.yaml      # 熔断规则配置
│   └── alert_config.yaml     # 告警规则配置
├── literature/
│   ├── pdf/                  # 文献 PDF 存储
│   └── structured/           # 结构化文献笔记
├── hypothesis/               # 创新点与技术拆解
├── code/                     # MTGNN/TimesNet/XGBoost 代码
├── experiment/               # 实验结果与日志
├── memory/                   # 持久记忆库
│   ├── idea_memory.json      # 创新点记忆
│   └── experiment_memory.json # 实验记忆
├── knowledge_base/           # Obsidian 知识库
└── report/                   # 最终报告
```

---

## 快速开始

### 步骤 1：环境配置

1. 复制 `.env.example` 为 `.env`
2. 填写你的配置信息：
   - OPENAI_API_KEY
   - ZOTERO_API_KEY
   - ALIYUN_SERVER_PASSWORD
   - GIT_REPO_URL

### 步骤 2：修改研究定义

编辑 `research_definition.md`，填写：
- 核心研究主题
- 核心关键词
- 评价指标
- 实验约束

### 步骤 3：启动 Cline

将 `docs/DARIS_Cline_Prompt.md` 内容发送给 Cline，启动自动化执行。

---

## 六智能体架构

| 智能体 | 职责 | 复用模块 |
|--------|------|----------|
| 研究管理智能体 | 流程调度、迭代决策 | EvoScientist+SciPhi |
| 文献调研智能体 | 文献检索、Zotero 归档 | OpenResearch+Zotero-GPT |
| 创新挖掘智能体 | 创新点发现与拆解 | AI-Scientist+PaperAgent |
| 工程实现智能体 | 代码实现与部署 | Aider+ML-Agent-Research |
| 实验调优智能体 | 云端调优与迭代 | ARIS+AutoResearch |
| 质量评估智能体 | 质量监控与合规检查 | ARIS+EvoScientist |

---

## 核心工作流环节

1. **项目初始化**：创建目录、校验配置、初始化 Git
2. **研究定义同步**：统一全流程规则
3. **文献调研**：检索、归档、结构化解析
4. **创新挖掘**：知识图谱、创新点生成、技术拆解
5. **代码实现**：基线复现、模块实现、云端同步
6. **实验调优**：自动迭代、指标评审、结果回传
7. **结果沉淀**：资产同步、迭代复盘

---

## 异常处理机制

| 异常场景 | 处理规则 | 重试策略 |
|----------|----------|----------|
| 文献检索失败 | 切换 API 源 | 单篇重试 3 次 |
| 代码运行报错 | Aider 自动修复 | 重试 5 次，失败回滚 |
| 阿里云连接失败 | 自动重试 | 重试 5 次，暂停告警 |
| 指标持续下降 | 回滚最优版本 | 连续 5 轮下降回滚 |

---

## 交付物

- 《DARIS 全流程执行报告》
- 三模型最优版本代码包
- 全量实验结果
- 全量科研资产
- 迭代复盘报告

---

## 许可证

MIT License