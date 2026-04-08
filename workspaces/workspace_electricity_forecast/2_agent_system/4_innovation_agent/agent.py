from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(str(Path(__file__).resolve().parents[1]))
from base_agent import BaseAgent, AgentIO


class InnovationAgent(BaseAgent):
    """
    创新点生成与技术拆解智能体（环节 3）
    
    绑定开源项目:
    - AI-Scientist: github.com/SakanaAI/AI-Scientist
    - PaperAgent: github.com/THUDM/PaperAgent
    
    复用核心模块:
    - 原子学术概念拆解模块
    - 研究假说生成模块
    - 基线短板分析模块
    - 原子化技术模块拆解模块
    
    指定执行大模型：glm-5（任务管理调度专用）
    兜底备用模型：qwen3.5-plus
    """
    
    name = "innovation_agent"
    description = "创新点生成与技术拆解智能体"
    
    # 绑定的开源项目仓库
    BOUND_REPOS = {
        "ai_scientist": "https://github.com/SakanaAI/AI-Scientist",
        "paperagent": "https://github.com/THUDM/PaperAgent",
    }
    
    # AI-Scientist 核心模块模拟
    AI_SCIENTIST_MODULES = {
        "concept_decompose": "原子学术概念拆解",
        "hypothesis_generate": "研究假说生成",
        "baseline_analysis": "基线短板分析",
        "module_decompose": "原子化技术模块拆解",
    }
    
    # 基线模型配置
    BASELINE_MODELS = {
        "mtgnn": {
            "name": "MTGNN",
            "description": "图神经网络时序预测模型",
            "key_components": ["图学习层", "时间卷积层", "自适应邻接矩阵"],
            "improvement_directions": ["动态图结构", "自适应感受野", "多尺度特征融合"],
        },
        "timesnet": {
            "name": "TimesNet",
            "description": "基于周期变换的时序预测模型",
            "key_components": ["周期检测", "2D 变换", "Inception 模块"],
            "improvement_directions": ["多周期融合", "物理约束嵌入", "残差解耦"],
        },
        "xgboost": {
            "name": "XGBoost",
            "description": "梯度提升树模型",
            "key_components": ["决策树集成", "正则化", "特征重要性"],
            "improvement_directions": ["特征工程优化", "超参自适应", "集成策略改进"],
        },
    }
    
    def __init__(self, env: Optional[Dict[str, str]] = None):
        super().__init__(env)
        self.innovation_dir = Path(__file__).resolve().parents[2] / "4_research_hypothesis"
    
    def validate_inputs(self, payload: Dict[str, Any]) -> None:
        """验证输入"""
        super().validate_inputs(payload)
        # 至少需要 literature_summary 或 research_context 之一
        if "literature_summary" not in payload and "research_context" not in payload:
            raise ValueError("Missing required field: literature_summary or research_context")
    
    def decompose_concepts(self, literature_summary: str) -> Dict[str, Any]:
        """
        原子学术概念拆解
        
        Args:
            literature_summary: 文献总结
        
        Returns:
            概念拆解结果
        """
        self.log("执行原子学术概念拆解")
        
        system_prompt = """你是 AI-Scientist 概念拆解专家，请将以下文献总结中的核心概念进行原子化拆解：

输出格式要求：
## 原子概念列表

### 概念名称
- 定义：[精确定义]
- 所属分类：[方法论/技术/评估指标]
- 关联研究：[相关文献/学者]
- 可组合性：[可与其他概念组合的方式]

请聚焦于时序预测、图神经网络、特征工程等方向的核心概念。"""
        
        user_prompt = f"文献总结:\n{literature_summary[:3000]}"
        
        response, model_used = self.llm_client.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            stage="innovation",  # 使用 glm-5
        )
        
        self.log(f"概念拆解完成，使用模型：{model_used}")
        
        return {
            "concept_decomposition": response,
            "model_used": model_used,
            "timestamp": datetime.now().isoformat(),
        }
    
    def generate_hypotheses(
        self,
        concept_decomposition: str,
        research_gaps: str,
    ) -> Dict[str, Any]:
        """
        研究假说生成
        
        Args:
            concept_decomposition: 概念拆解结果
            research_gaps: 研究空白分析
        
        Returns:
            研究假说列表
        """
        self.log("生成研究假说")
        
        system_prompt = """你是 AI-Scientist 假说生成专家，请基于以下概念拆解和研究空白，生成 3-5 个可验证的研究假说：

输出格式要求：
## 研究假说列表

### 假说 1: [假说名称]
- 核心主张：[清晰陈述假说内容]
- 理论依据：[支撑该假说的理论基础]
- 验证方法：[如何设计实验验证]
- 预期贡献：[如果假说成立，有什么贡献]
- 风险评估：[可能的失败原因]

请确保假说具有可验证性、创新性和实用价值。"""
        
        user_prompt = f"""概念拆解:
{concept_decomposition[:2000]}

研究空白:
{research_gaps[:2000]}"""
        
        response, model_used = self.llm_client.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            stage="innovation",
        )
        
        self.log(f"假说生成完成，使用模型：{model_used}")
        
        return {
            "hypotheses": response,
            "model_used": model_used,
            "timestamp": datetime.now().isoformat(),
        }
    
    def analyze_baseline_weaknesses(self, baseline_models: List[str] = None) -> Dict[str, Any]:
        """
        基线短板分析
        
        Args:
            baseline_models: 基线模型列表
        
        Returns:
            基线短板分析
        """
        self.log("分析基线模型短板")
        
        if baseline_models is None:
            baseline_models = ["mtgnn", "timesnet", "xgboost"]
        
        analysis = {}
        for model_key in baseline_models:
            if model_key in self.BASELINE_MODELS:
                model_info = self.BASELINE_MODELS[model_key]
                analysis[model_key] = {
                    "name": model_info["name"],
                    "description": model_info["description"],
                    "key_components": model_info["key_components"],
                    "potential_weaknesses": self._analyze_model_weaknesses(model_info),
                    "improvement_directions": model_info["improvement_directions"],
                }
        
        # 使用 glm-5 进行深度分析
        system_prompt = """你是基线模型分析专家，请深入分析以下基线模型的潜在短板：

MTGNN: 图神经网络时序预测模型
TimesNet: 基于周期变换的时序预测模型  
XGBoost: 梯度提升树模型

针对每个模型，请分析：
1. 当前方法的核心局限性
2. 在电力负荷预测场景下的不足
3. 可能的改进切入点

请用结构化格式输出。"""
        
        user_prompt = "请分析 MTGNN、TimesNet、XGBoost 三个基线模型的短板"
        
        response, model_used = self.llm_client.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            stage="innovation",
        )
        
        self.log(f"基线短板分析完成，使用模型：{model_used}")
        
        return {
            "baseline_analysis": response,
            "model_analysis": analysis,
            "model_used": model_used,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _analyze_model_weaknesses(self, model_info: Dict[str, Any]) -> List[str]:
        """分析单个模型的潜在弱点"""
        weaknesses = []
        
        if model_info["name"] == "MTGNN":
            weaknesses = [
                "静态图结构无法适应动态变化的时序关系",
                "自适应邻接矩阵可能过拟合训练数据",
                "对长序列依赖建模能力有限",
                "缺乏物理约束，预测结果可能不符合实际",
            ]
        elif model_info["name"] == "TimesNet":
            weaknesses = [
                "周期检测对非平稳序列敏感",
                "2D 变换增加计算复杂度",
                "多周期融合机制不够完善",
                "对突发事件响应能力不足",
            ]
        elif model_info["name"] == "XGBoost":
            weaknesses = [
                "难以捕捉时序依赖关系",
                "特征工程依赖人工经验",
                "对长时序预测效果有限",
                "缺乏对多变量相关性的建模",
            ]
        
        return weaknesses
    
    def decompose_innovation_modules(
        self,
        hypotheses: str,
        baseline_weaknesses: str,
    ) -> Dict[str, Any]:
        """
        原子化技术模块拆解
        
        Args:
            hypotheses: 研究假说
            baseline_weaknesses: 基线短板分析
        
        Returns:
            技术模块拆解结果
        """
        self.log("拆解创新点为可执行的技术模块")
        
        system_prompt = """你是技术模块拆解专家，请将以下研究假说和创新点拆解为可独立编码验证的原子化技术模块：

输出格式要求：
## 技术模块列表

### 模块名称
- 功能描述：[模块实现的具体功能]
- 输入输出：[数据接口定义]
- 依赖关系：[与其他模块的依赖]
- 实现优先级：[P0/P1/P2]
- 预估工作量：[人天]
- 验证标准：[如何验证模块功能正确]

请将每个创新点拆解为 3-5 个可独立实现的技术模块。"""
        
        user_prompt = f"""研究假说:
{hypotheses[:2000]}

基线短板:
{baseline_weaknesses[:2000]}

请将上述创新点拆解为可执行的技术模块。"""
        
        response, model_used = self.llm_client.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            stage="innovation",
        )
        
        self.log(f"技术模块拆解完成，使用模型：{model_used}")
        
        return {
            "module_decomposition": response,
            "model_used": model_used,
            "timestamp": datetime.now().isoformat(),
        }
    
    def generate_innovation_proposal(
        self,
        literature_context: str,
        hypotheses: str,
        module_decomposition: str,
    ) -> Dict[str, Any]:
        """
        生成完整的创新点提案
        
        Args:
            literature_context: 文献背景
            hypotheses: 研究假说
            module_decomposition: 模块拆解
        
        Returns:
            创新点提案
        """
        self.log("生成完整创新点提案")
        
        system_prompt = """你是科研创新提案专家，请整合以下分析结果，生成一份完整的创新点提案：

输出格式要求：
# 创新点提案

## 1. 研究背景与动机
- 问题定义
- 研究意义

## 2. 创新点概述
- 创新点 1: [名称 + 简述]
- 创新点 2: [名称 + 简述]
- 创新点 3: [名称 + 简述]

## 3. 技术路线
- 整体架构
- 关键技术
- 实现步骤

## 4. 预期成果
- 理论贡献
- 实践价值

## 5. 风险评估与应对
- 潜在风险
- 应对策略

## 6. 评估指标
- 主要指标（MAE/RMSE/R²）
- 辅助指标（稳定性/效率）

请确保提案内容具体、可执行、可验证。"""
        
        user_prompt = f"""文献背景:
{literature_context[:1500]}

研究假说:
{hypotheses[:1500]}

技术模块拆解:
{module_decomposition[:1500]}

请生成完整的创新点提案。"""
        
        response, model_used = self.llm_client.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            stage="innovation",
        )
        
        self.log(f"创新点提案完成，使用模型：{model_used}")
        
        return {
            "innovation_proposal": response,
            "model_used": model_used,
            "timestamp": datetime.now().isoformat(),
        }
    
    def save_innovation(self, results: Dict[str, Any]) -> Path:
        """保存创新点结果"""
        self.innovation_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存 JSON 格式
        json_path = self.innovation_dir / f"innovation_{timestamp}.json"
        json_path.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        # 保存 Markdown 格式（创新点列表）
        md_path = self.innovation_dir / f"innovation_list_{timestamp}.md"
        md_content = f"""# 创新点提案

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**使用模型**: {results.get('model_used', 'glm-5')}

---

{results.get('innovation_proposal', {}).get('innovation_proposal', '暂无数据')}

---

## 附录

### 概念拆解
{results.get('concept_decomposition', {}).get('concept_decomposition', '暂无数据')}

### 研究假说
{results.get('hypotheses', {}).get('hypotheses', '暂无数据')}

### 基线短板分析
{results.get('baseline_weaknesses', {}).get('baseline_analysis', '暂无数据')}

### 技术模块拆解
{results.get('module_decomposition', {}).get('module_decomposition', '暂无数据')}
"""
        md_path.write_text(md_content, encoding="utf-8")
        
        # 保存创新点列表（简化版）
        innovation_list_path = self.innovation_dir / "innovation_list.md"
        innovation_list_path.write_text(md_content, encoding="utf-8")
        
        self.log(f"创新点结果已保存：{md_path}")
        
        return md_path
    
    def run(self, payload: Dict[str, Any]) -> AgentIO:
        """
        执行创新点生成
        
        Args:
            payload: 包含 literature_summary, research_context 等
        
        Returns:
            AgentIO 包含创新点提案
        """
        self.validate_inputs(payload)
        
        literature_summary = payload.get("literature_summary", "")
        research_context = payload.get("research_context", "")
        research_gaps = payload.get("research_gaps", "")
        
        # 加载文献总结文件
        if payload.get("literature_path"):
            lit_path = Path(payload["literature_path"])
            if lit_path.exists():
                data = json.loads(lit_path.read_text(encoding="utf-8"))
                if not literature_summary:
                    literature_summary = data.get("summary", "")
                    research_gaps = data.get("research_gaps", {}).get("research_gaps", "")
        
        self.log("开始生成创新点")
        
        results = {
            "concept_decomposition": {},
            "hypotheses": {},
            "baseline_weaknesses": {},
            "module_decomposition": {},
            "innovation_proposal": {},
            "execution_log": [],
        }
        
        # 1. 概念拆解
        results["concept_decomposition"] = self.decompose_concepts(literature_summary)
        
        # 2. 基线短板分析
        results["baseline_weaknesses"] = self.analyze_baseline_weaknesses()
        
        # 3. 假说生成
        results["hypotheses"] = self.generate_hypotheses(
            results["concept_decomposition"].get("concept_decomposition", ""),
            research_gaps,
        )
        
        # 4. 技术模块拆解
        results["module_decomposition"] = self.decompose_innovation_modules(
            results["hypotheses"].get("hypotheses", ""),
            results["baseline_weaknesses"].get("baseline_analysis", ""),
        )
        
        # 5. 生成完整创新点提案
        results["innovation_proposal"] = self.generate_innovation_proposal(
            literature_summary[:1500] + research_context[:1500],
            results["hypotheses"].get("hypotheses", ""),
            results["module_decomposition"].get("module_decomposition", ""),
        )
        
        results["execution_log"] = self.get_execution_log()
        
        # 保存结果
        innovation_path = self.save_innovation(results)
        
        # 保存调用日志
        log_dir = Path(__file__).resolve().parents[2] / "7_monitor_system" / "system_log"
        self.llm_client.save_call_log(log_dir / f"innovation_agent_call_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        result = {
            "status": "completed",
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "innovation_path": str(innovation_path),
            "model_used": "glm-5",
            "execution_log": self.get_execution_log(),
        }
        
        return AgentIO(inputs=payload, outputs=result)