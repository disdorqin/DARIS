from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(str(Path(__file__).resolve().parents[1]))
from base_agent import BaseAgent, AgentIO


class InnovationReviewAgent(BaseAgent):
    """
    创新点可行性评审智能体（环节 4）
    
    绑定开源项目:
    - ARIS: github.com/OpenBMB/ARIS
    
    复用核心模块:
    - 执行 + 评审双模型验证体系
    - 创新点可行性校验模块
    - 落地风险评估模块
    - 优先级排序模块
    
    指定执行大模型：MiniMax-M2.5（评审专用）
    兜底备用模型：qwen3.5-plus
    """
    
    name = "innovation_review_agent"
    description = "创新点可行性评审智能体"
    
    # 绑定的开源项目仓库
    BOUND_REPOS = {
        "aris": "https://github.com/OpenBMB/ARIS",
    }
    
    # ARIS 核心模块模拟
    ARIS_MODULES = {
        "dual_model_validation": "执行 + 评审双模型验证体系",
        "feasibility_check": "创新点可行性校验",
        "risk_assessment": "落地风险评估",
        "priority_ranking": "优先级排序",
    }
    
    # 评审维度
    REVIEW_DIMENSIONS = {
        "feasibility": "可行性（技术是否可落地）",
        "novelty": "新颖性（是否有足够创新）",
        "impact": "影响力（对性能提升的预期）",
        "risk": "风险等级（实施难度和失败概率）",
        "clarity": "清晰度（方案描述是否明确）",
    }
    
    def __init__(self, env: Optional[Dict[str, str]] = None):
        super().__init__(env)
        self.review_dir = Path(__file__).resolve().parents[2] / "4_research_hypothesis" / "review_report"
    
    def validate_inputs(self, payload: Dict[str, Any]) -> None:
        """验证输入"""
        super().validate_inputs(payload)
        if "innovation_proposal" not in payload and "innovation_path" not in payload:
            raise ValueError("Missing required field: innovation_proposal or innovation_path")
    
    def dual_model_validation(
        self,
        innovation_proposal: str,
    ) -> Dict[str, Any]:
        """
        执行 + 评审双模型验证体系
        
        Args:
            innovation_proposal: 创新点提案
        
        Returns:
            双模型验证结果
        """
        self.log("执行双模型验证")
        
        # 执行模型视角：评估可执行性
        executor_prompt = """你是 ARIS 执行模型，请从实施角度评估以下创新点提案：

关注点：
1. 技术实现的具体步骤是否清晰
2. 所需资源和依赖是否明确
3. 工作量估算是否合理
4. 是否存在技术障碍

请输出执行可行性评估报告。"""
        
        user_prompt = f"创新点提案:\n{innovation_proposal[:3000]}"
        
        executor_response, _ = self.llm_client.call(
            system_prompt=executor_prompt,
            user_prompt=user_prompt,
            model="qwen3.5-plus",  # 执行模型使用 qwen
            stage="innovation_review",
        )
        
        # 评审模型视角：评估质量和风险（使用 MiniMax-M2.5）
        critic_prompt = """你是 ARIS 评审模型，请从质量角度严格评审以下创新点提案：

关注点：
1. 创新性是否足够
2. 与现有方法的差异是否明确
3. 预期收益是否合理
4. 潜在风险是否被充分识别

请输出质量评审报告，给出明确的通过/修改/驳回建议。"""
        
        critic_response, model_used = self.llm_client.call(
            system_prompt=critic_prompt,
            user_prompt=user_prompt,
            stage="innovation_review",  # 使用 MiniMax-M2.5
        )
        
        self.log(f"双模型验证完成，评审模型：{model_used}")
        
        return {
            "executor_report": executor_response,
            "critic_report": critic_response,
            "model_used": model_used,
            "timestamp": datetime.now().isoformat(),
        }
    
    def feasibility_check(self, innovation_proposal: str) -> Dict[str, Any]:
        """
        创新点可行性校验
        
        Args:
            innovation_proposal: 创新点提案
        
        Returns:
            可行性校验结果
        """
        self.log("执行可行性校验")
        
        system_prompt = """你是 ARIS 可行性校验专家，请按以下维度评估创新点的可行性：

## 评估维度

### 1. 技术可行性 (0-10 分)
- 现有技术是否支持
- 技术难度评估
- 所需技能匹配度

### 2. 资源可行性 (0-10 分)
- 计算资源需求
- 数据资源需求
- 时间资源需求

### 3. 方法可行性 (0-10 分)
- 方案描述清晰度
- 实施步骤完整性
- 验证方法可执行性

### 4. 综合评估
- 总分 (0-30 分)
- 可行性等级 (高/中/低)
- 关键风险点
- 建议措施

请给出具体评分和详细理由。"""
        
        user_prompt = f"创新点提案:\n{innovation_proposal[:3000]}"
        
        response, model_used = self.llm_client.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            stage="innovation_review",
        )
        
        self.log(f"可行性校验完成，使用模型：{model_used}")
        
        return {
            "feasibility_report": response,
            "model_used": model_used,
            "timestamp": datetime.now().isoformat(),
        }
    
    def risk_assessment(self, innovation_proposal: str) -> Dict[str, Any]:
        """
        落地风险评估
        
        Args:
            innovation_proposal: 创新点提案
        
        Returns:
            风险评估结果
        """
        self.log("执行风险评估")
        
        system_prompt = """你是 ARIS 风险评估专家，请识别以下创新点提案的潜在风险：

## 风险评估框架

### 技术风险
- 技术实现难度超预期
- 依赖技术不稳定
- 性能不达标

### 数据风险
- 数据质量不足
- 数据量不足
- 特征工程困难

### 资源风险
- 计算资源不足
- 时间预算不足
- 人力资源不足

### 外部风险
- 竞品抢先发布
- 技术路线被证伪
- 合作依赖风险

### 风险等级评定
- 高风险：可能导致项目失败
- 中风险：可能影响进度或性能
- 低风险：可控范围内

请针对每个识别的风险，给出：
1. 风险描述
2. 发生概率 (高/中/低)
3. 影响程度 (高/中/低)
4. 应对策略"""
        
        user_prompt = f"创新点提案:\n{innovation_proposal[:3000]}"
        
        response, model_used = self.llm_client.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            stage="innovation_review",
        )
        
        self.log(f"风险评估完成，使用模型：{model_used}")
        
        return {
            "risk_report": response,
            "model_used": model_used,
            "timestamp": datetime.now().isoformat(),
        }
    
    def priority_ranking(
        self,
        innovations: List[Dict[str, Any]],
        feasibility: str,
        risks: str,
    ) -> Dict[str, Any]:
        """
        优先级排序
        
        Args:
            innovations: 创新点列表
            feasibility: 可行性评估
            risks: 风险评估
        
        Returns:
            优先级排序结果
        """
        self.log("执行优先级排序")
        
        system_prompt = """你是 ARIS 优先级排序专家，请根据可行性和风险评估结果，对创新点进行优先级排序：

## 排序规则

### P0（最高优先级）
- 可行性高 + 风险低 + 预期收益高
- 建议立即执行

### P1（高优先级）
- 可行性中 + 风险中 + 预期收益高
- 建议在 P0 之后执行

### P2（中优先级）
- 可行性中 + 风险中 + 预期收益中
- 建议视资源情况执行

### P3（低优先级）
- 可行性低 或 风险高
- 建议暂缓或重新设计

请输出每个创新点的优先级评定及理由。"""
        
        user_prompt = f"""可行性评估:
{feasibility[:2000]}

风险评估:
{risks[:2000]}

请对创新点进行优先级排序。"""
        
        response, model_used = self.llm_client.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            stage="innovation_review",
        )
        
        self.log(f"优先级排序完成，使用模型：{model_used}")
        
        return {
            "priority_ranking": response,
            "model_used": model_used,
            "timestamp": datetime.now().isoformat(),
        }
    
    def generate_review_report(
        self,
        innovation_proposal: str,
        dual_validation: Dict[str, Any],
        feasibility: Dict[str, Any],
        risks: Dict[str, Any],
        priority: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        生成完整评审报告
        
        Args:
            innovation_proposal: 创新点提案
            dual_validation: 双模型验证结果
            feasibility: 可行性评估
            risks: 风险评估
            priority: 优先级排序
        
        Returns:
            完整评审报告
        """
        self.log("生成评审报告")
        
        # 使用 MiniMax-M2.5 生成最终评审报告
        system_prompt = """你是 ARIS 评审报告生成专家，请整合以下评估结果，生成一份完整的评审报告：

## 评审报告格式

# 创新点评审报告

## 1. 评审概要
- 评审时间
- 评审对象
- 评审结论（通过/修改后通过/驳回）

## 2. 双模型验证结果
### 2.1 执行模型评估
[执行可行性评估摘要]

### 2.2 评审模型评估
[质量评审摘要]

## 3. 可行性评估
[可行性评分和详细分析]

## 4. 风险评估
[识别的主要风险及应对策略]

## 5. 优先级排序
[各创新点的优先级评定]

## 6. 评审结论
### 6.1 通过项
[可以直接执行的内容]

### 6.2 风险项
[需要注意的风险点]

### 6.3 必须修改项
[必须修改后才能执行的内容]

## 7. 执行建议
[具体的执行建议和注意事项]

请确保评审结论明确、具体、可执行。"""
        
        user_prompt = f"""创新点提案:
{innovation_proposal[:2000]}

执行模型评估:
{dual_validation.get('executor_report', '')[:1500]}

评审模型评估:
{dual_validation.get('critic_report', '')[:1500]}

可行性评估:
{feasibility.get('feasibility_report', '')[:1500]}

风险评估:
{risks.get('risk_report', '')[:1500]}

优先级排序:
{priority.get('priority_ranking', '')[:1500]}

请生成完整的评审报告。"""
        
        response, model_used = self.llm_client.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            stage="innovation_review",
        )
        
        self.log(f"评审报告生成完成，使用模型：{model_used}")
        
        return {
            "review_report": response,
            "model_used": model_used,
            "timestamp": datetime.now().isoformat(),
        }
    
    def save_review(self, results: Dict[str, Any]) -> Path:
        """保存评审结果"""
        self.review_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存 JSON 格式
        json_path = self.review_dir / f"review_{timestamp}.json"
        json_path.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        # 保存 Markdown 格式（评审报告）
        md_path = self.review_dir / f"review_report_{timestamp}.md"
        md_content = f"""# 创新点评审报告

**评审时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**评审模型**: {results.get('model_used', 'MiniMax-M2.5')}

---

{results.get('review_report', {}).get('review_report', '暂无数据')}

---

## 附录

### 双模型验证
#### 执行模型评估
{results.get('dual_validation', {}).get('executor_report', '暂无数据')}

#### 评审模型评估
{results.get('dual_validation', {}).get('critic_report', '暂无数据')}

### 可行性评估
{results.get('feasibility', {}).get('feasibility_report', '暂无数据')}

### 风险评估
{results.get('risks', {}).get('risk_report', '暂无数据')}

### 优先级排序
{results.get('priority', {}).get('priority_ranking', '暂无数据')}
"""
        md_path.write_text(md_content, encoding="utf-8")
        
        self.log(f"评审结果已保存：{md_path}")
        
        return md_path
    
    def run(self, payload: Dict[str, Any]) -> AgentIO:
        """
        执行创新点评审
        
        Args:
            payload: 包含 innovation_proposal 或 innovation_path
        
        Returns:
            AgentIO 包含评审报告
        """
        self.validate_inputs(payload)
        
        innovation_proposal = payload.get("innovation_proposal", "")
        
        # 从文件加载创新点提案
        if not innovation_proposal and payload.get("innovation_path"):
            innov_path = Path(payload["innovation_path"])
            if innov_path.exists():
                data = json.loads(innov_path.read_text(encoding="utf-8"))
                innovation_proposal = data.get("innovation_proposal", {}).get("innovation_proposal", "")
        
        if not innovation_proposal:
            return AgentIO(
                inputs=payload,
                outputs={
                    "status": "error",
                    "message": "No innovation proposal provided or loaded",
                }
            )
        
        self.log("开始创新点评审")
        
        results = {
            "dual_validation": {},
            "feasibility": {},
            "risks": {},
            "priority": {},
            "review_report": {},
            "execution_log": [],
        }
        
        # 1. 双模型验证
        results["dual_validation"] = self.dual_model_validation(innovation_proposal)
        
        # 2. 可行性校验
        results["feasibility"] = self.feasibility_check(innovation_proposal)
        
        # 3. 风险评估
        results["risks"] = self.risk_assessment(innovation_proposal)
        
        # 4. 优先级排序
        results["priority"] = self.priority_ranking(
            [{"proposal": innovation_proposal}],
            results["feasibility"].get("feasibility_report", ""),
            results["risks"].get("risk_report", ""),
        )
        
        # 5. 生成评审报告
        results["review_report"] = self.generate_review_report(
            innovation_proposal,
            results["dual_validation"],
            results["feasibility"],
            results["risks"],
            results["priority"],
        )
        
        results["execution_log"] = self.get_execution_log()
        
        # 保存结果
        review_path = self.save_review(results)
        
        # 保存调用日志
        log_dir = Path(__file__).resolve().parents[2] / "7_monitor_system" / "system_log"
        self.llm_client.save_call_log(log_dir / f"innovation_review_call_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        result = {
            "status": "completed",
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "review_path": str(review_path),
            "model_used": "MiniMax-M2.5",
            "execution_log": self.get_execution_log(),
        }
        
        return AgentIO(inputs=payload, outputs=result)