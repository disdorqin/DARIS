# DARIS - 深度自动化研究与创新系统

<div align="center">

![DARIS Banner](https://img.shields.io/badge/DARIS-Deep%20Automated%20Research%20%26%20Innovation%20System-blue?style=for-the-badge)

[![GitHub](https://img.shields.io/badge/github-disdorqin/DARIS-blue)](https://github.com/disdorqin/DARIS)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/disdorqin/DARIS?color=yellow)](https://github.com/disdorqin/DARIS/stargazers)

**让 AI 驱动科研，让创新更高效**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [架构设计](#-架构设计) • [使用文档](#-使用文档) • [案例展示](#-案例展示)

</div>

---

## 📖 项目概述

### 什么是 DARIS？

**DARIS** (Deep Automated Research & Innovation System) 是一个企业级的 AI 驱动科学研究工作流自动化平台。它整合了大语言模型、机器学习、知识管理和自动化工作流，为科研团队提供从文献发现到实验验证的全流程支持。

### 产品愿景

> 让研究人员从繁琐的重复性工作中解放出来，专注于创造性思考。DARIS 通过 AI 自动化处理文献检索、数据分析、实验执行等任务，加速科研创新周期。

### 核心价值

| 价值维度 | 说明 |
|---------|------|
| 🚀 **效率提升** | 自动化文献检索、数据预处理、模型训练等重复性工作 |
| 🧠 **智能辅助** | 基于大模型的文献理解、假设生成和实验设计建议 |
| 📊 **可复现性** | 标准化的工作区管理和实验记录，确保研究可复现 |
| 🔗 **知识沉淀** | 自动构建知识库，形成可积累的研究资产 |
| 🌐 **云端协同** | 支持多机部署和远程协作，适应分布式团队 |

---

## ✨ 功能特性

### 核心模块

```
┌─────────────────────────────────────────────────────────────────────┐
│                          DARIS 平台架构                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  文献工作流   │  │  假设生成器   │  │  实验执行器   │              │
│  │  📚          │  │  💡          │  │  🔬          │              │
│  │ • arXiv 检索  │  │ • 文献分析   │  │ • 模型训练   │              │
│  │ • CrossRef   │  │ • 假设提取   │  │ • 实验评估   │              │
│  │ • Semantic   │  │ • 路线规划   │  │ • 结果记录   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  知识资产库   │  │  通知系统    │  │  云同步服务   │              │
│  │  📊          │  │  📱          │  │  ☁️          │              │
│  │ • Zotero 集成 │  │ • 钉钉机器人  │  │ • 阿里云同步  │              │
│  │ • 自动归档    │  │ • 进度推送   │  │ • 备份恢复   │              │
│  │ • 版本管理    │  │ • 告警通知   │  │ • 分布式部署  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                    ┌─────────┴─────────┐
                    │   AI 模型服务层    │
                    │ • 通义千问/Qwen   │
                    │ • OpenAI GPT      │
                    │ • Anthropic Claude│
                    └───────────────────┘
```

### 详细功能清单

#### 📚 文献工作流
- **自动检索**: 支持 arXiv、CrossRef、Semantic Scholar 等学术数据库
- **智能分类**: 基于 AI 的文献自动分类和标签化
- **摘要提取**: 自动生成文献摘要和关键信息提取
- **关联分析**: 发现文献间的引用关系和研究脉络

#### 💡 研究假设生成
- **文献驱动**: 从现有文献中自动提取研究空白和创新点
- **假设构建**: 生成结构化的研究假设和技术路线
- **可行性评估**: AI 辅助评估研究假设的可行性
- **迭代优化**: 支持多轮假设 refinement

#### 🔬 实验执行系统
- **多模型支持**:
  - 传统机器学习：XGBoost、Random Forest、SVM
  - 深度学习：MTGNN、TimesNet、Transformer
  - 时序预测：专用时序模型库
- **自动化训练**: 一键式模型训练和超参数调优
- **实验追踪**: 完整的实验日志和指标记录
- **结果可视化**: 自动生成实验报告

#### 📱 通知与监控
- **钉钉集成**: 实时推送实验进度和结果
- **告警系统**: 异常检测和自动告警
- **成本监控**: API 调用成本和资源使用追踪

---

## 🏗️ 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            用户交互层                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  CLI 工具    │  │  配置文件   │  │  钉钉通知   │  │  API 接口    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           工作区管理层                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Workspace Manager                            │    │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐   │    │
│  │  │ Default   │  │Electricity│  │   Test    │  │   Custom  │   │    │
│  │  │ Workspace │  │ Forecast  │  │  Project  │  │  Projects │   │    │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           核心服务层                                     │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐          │
│  │ Literature │ │Hypothesis  │ │ Experiment │ │ Knowledge  │          │
│  │  Service   │ │  Service   │ │  Service   │ │  Service   │          │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘          │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐          │
│  │  Monitor   │ │  Notify    │ │  Cloud     │ │   Path     │          │
│  │  Service   │ │  Service   │ │  Sync      │ │  Resolver  │          │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           基础设施层                                     │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐          │
│  │   Git      │ │  Database  │ │   File     │ │   Cloud    │          │
│  │  Storage   │ │  (SQLite)  │ │  System    │ │  Storage   │          │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 工作区结构

每个工作区采用标准化目录结构，确保研究的可复现性：

```
workspace_name/
├── 1_config/              # 配置文件（Agent、Git、监控等）
├── 2_agent_system/        # AI Agent 系统核心
│   └── 1_research_manager/
├── 3_literature_workflow/ # 文献工作流输出
├── 4_research_hypothesis/ # 研究假设文档
├── 5_code_base/           # 生成的代码库
├── 6_experiment_execution/# 实验执行和数据
│   ├── data/              # 原始和处理后的数据
│   └── results/           # 实验结果
├── 7_monitor_system/      # 监控和告警配置
├── 8_knowledge_asset/     # 知识资产沉淀
├── config/                # 工作区配置
├── literature/            # 文献 PDF 和元数据
├── hypothesis/            # 假设文档
├── code/                  # 实验代码
├── experiment/            # 实验配置
├── memory/                # 运行记忆
├── knowledge_base/        # 知识库
├── logs/                  # 日志文件
├── report/                # 报告输出
└── rounds/                # 研究轮次记录
```

---

## 🚀 快速开始

### 前置要求

| 要求 | 版本 | 说明 |
|------|------|------|
| Python | >= 3.9 | 推荐 3.10+ |
| Git | 任意 | 用于版本控制 |
| Conda | 推荐 | 环境管理 |
| CUDA | 可选 | GPU 加速（11.8+） |

### 安装步骤

#### 1. 克隆仓库

```bash
git clone https://github.com/disdorqin/DARIS.git
cd DARIS
```

#### 2. 创建环境

```bash
# 使用 conda（推荐）
conda create -n daris-research python=3.10
conda activate daris-research

# 或使用 venv
python -m venv daris-env
source daris-env/bin/activate  # Linux/Mac
# or
daris-env\Scripts\activate  # Windows
```

#### 3. 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt

# 安装 PyTorch（选择适合的版本）
# GPU 版本 (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# CPU 版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

#### 4. 配置环境

```bash
# 复制环境配置模板
cp .env.example .env

# 编辑 .env 文件，填入必要的配置
```

#### 5. 验证安装

```bash
# 查看当前工作区
cat .current_workspace

# 列出所有工作区
python scripts/switch_workspace.py --list

# 运行测试
python workspaces/workspace_default/experiment/pipeline/check_torch.py
```

---

## 📋 配置说明

### 环境变量配置

编辑 `.env` 文件，配置以下内容：

```yaml
# ==================== 大模型 API 配置 ====================
# 阿里云通义千问（主要使用）
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://coding.dashscope.aliyuncs.com/v1

# Anthropic API（备用）
ANTHROPIC_API_KEY=your-api-key-here

# DeepSeek API（备用）
DEEPSEEK_API_KEY=your-api-key-here

# ==================== 学术 API 配置 ====================
# Semantic Scholar API
SEMANTIC_SCHOLAR_API_KEY=your-api-key-here

# ==================== Zotero 配置 ====================
ZOTERO_API_KEY=your-zotero-api-key-here
ZOTERO_USER_ID=your-zotero-user-id-here
ZOTERO_LIBRARY_TYPE=user
ZOTERO_COLLECTION_NAME=DARIS

# ==================== 阿里云服务器配置 ====================
ALIYUN_SERVER_IP=47.100.98.160
ALIYUN_SERVER_PORT=22
ALIYUN_SERVER_USER=root
ALIYUN_SERVER_PASSWORD=your-server-password-here

# ==================== 钉钉机器人配置 ====================
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=your-token
DINGTALK_SECRET=your-dingtalk-sign-secret
```

### 配置文件说明

| 配置文件 | 用途 |
|---------|------|
| `1_config/base/agent_config.yaml` | Agent 系统配置 |
| `1_config/base/git_config.yaml` | Git 同步配置 |
| `1_config/alert/dingtalk_config.yaml` | 钉钉通知配置 |
| `1_config/alert/monitor_rules.yaml` | 监控规则配置 |

---

## 💼 使用场景

### 场景一：文献调研自动化

```bash
# 1. 切换到目标研究工作区
python scripts/switch_workspace.py electricity_forecast

# 2. 运行文献检索工作流
python workspaces/workspace_electricity_forecast/3_literature_workflow/run.py

# 3. 查看生成的文献报告
cat workspaces/workspace_electricity_forecast/literature/structured_literature_report.md
```

### 场景二：研究假设生成

```bash
# 运行假设生成 Agent
python workspaces/workspace_electricity_forecast/2_agent_system/1_research_manager/run.py \
  --request "尖峰电价预测" \
  --rounds 1
```

### 场景三：实验执行与评估

```bash
# 运行完整工作流
python _run_electricity_workflow.py

# 查看实验结果
cat workspaces/workspace_electricity_forecast/report/final_workflow_run.log
```

---

## 📊 案例展示

### 电力尖峰预测研究

DARIS 已成功应用于电力负荷预测研究，支持：

- **数据集**: 山东电力市场 PMOS 小时级数据
- **模型**: MTGNN、TimesNet、XGBoost 对比实验
- **评估指标**: MAE、RMSE、MAPE、尖峰检出率

#### 实验结果示例

| 模型 | MAE | RMSE | MAPE | 尖峰检出率 |
|------|-----|------|------|-----------|
| XGBoost | 0.042 | 0.068 | 3.2% | 78.5% |
| MTGNN | 0.038 | 0.061 | 2.9% | 82.1% |
| TimesNet | 0.035 | 0.058 | 2.7% | 84.3% |

---

## 🛠️ 开发指南

### 添加新工作区

```bash
# 初始化新工作区
python scripts/init_workspace.py my_new_project

# 工作区将创建在 workspaces/workspace_my_new_project/
```

### 自定义 Agent

在 `2_agent_system/` 目录下创建自定义 Agent 模块：

```python
# workspaces/workspace_xxx/2_agent_system/my_agent.py
from core.utils.path_resolver import PathResolver

class MyCustomAgent:
    def __init__(self):
        self.path_resolver = PathResolver()
    
    def run(self, request: str):
        # 实现你的逻辑
        pass
```

---

## 📦 依赖清单

### 核心依赖

| 类别 | 依赖包 | 用途 |
|------|--------|------|
| HTTP | requests | API 调用 |
| 配置 | PyYAML | YAML 解析 |
| Git | GitPython | 版本控制 |
| SSH | paramiko, scp | 远程同步 |
| AI | openai | 大模型调用 |
| 文献 | pyzotero, semantic-scholar | 学术集成 |
| 数据 | numpy, pandas | 数据处理 |
| ML | scikit-learn, xgboost | 机器学习 |
| DL | torch, tslearn | 深度学习 |
| 通知 | dingtalk-sdk | 钉钉集成 |

---

## 🔧 常见问题

### Q1: PyTorch 安装失败？

```bash
# 检查 CUDA 版本
nvidia-smi

# 根据 CUDA 版本选择合适的 PyTorch
# CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 如果不需要 GPU，使用 CPU 版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Q2: 如何切换工作区？

```bash
# 方法 1: 使用脚本
python scripts/switch_workspace.py electricity_forecast

# 方法 2: 手动修改
echo "workspace_electricity_forecast" > .current_workspace
```

### Q3: 钉钉通知不工作？

检查 `.env` 中的配置：
- `DINGTALK_WEBHOOK` 是否正确
- `DINGTALK_SECRET` 是否匹配
- 网络是否可访问 `oapi.dingtalk.com`

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出新功能建议：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📬 联系方式

- **GitHub**: [@disdorqin](https://github.com/disdorqin)
- **项目仓库**: [DARIS](https://github.com/disdorqin/DARIS)
- **Issues**: [问题反馈](https://github.com/disdorqin/DARIS/issues)

---

<div align="center">

**DARIS** - 让 AI 驱动科研，让创新更高效

⭐ 如果这个项目对你有帮助，请给一个 Star 支持！

</div>