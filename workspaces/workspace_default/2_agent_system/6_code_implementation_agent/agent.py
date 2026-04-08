from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.append(str(Path(__file__).resolve().parents[1]))
from base_agent import BaseAgent, AgentIO


class CodeImplementationAgent(BaseAgent):
    """
    创新点代码实现智能体（环节 5 和 6）
    
    绑定开源项目:
    - Aider: github.com/paul-gauthier/aider
    - ML-Agent-Research: github.com/google/ml-agent-research
    
    复用核心模块:
    - 增量编码模块
    - 报错自动修复模块
    - 最小化验证模块
    - 公式↔代码双向映射模块
    - 基线代码适配模块
    - 增量代码集成模块
    - 阿里云同步模块
    - 代码报错自动修复模块
    
    指定执行大模型：qwen3.5-plus（代码书写专用）
    兜底备用模型：glm-5
    """
    
    name = "code_implementation_agent"
    description = "创新点代码实现智能体"
    
    # 绑定的开源项目仓库
    BOUND_REPOS = {
        "aider": "https://github.com/paul-gauthier/aider",
        "ml_agent_research": "https://github.com/google/ml-agent-research",
    }
    
    # Aider 核心模块模拟
    AIDER_MODULES = {
        "incremental_coding": "增量编码",
        "auto_fix": "报错自动修复",
        "minimal_validation": "最小化验证",
        "formula_code_mapping": "公式↔代码双向映射",
    }
    
    # ML-Agent-Research 核心模块模拟
    ML_AGENT_MODULES = {
        "baseline_adaptation": "基线代码适配",
        "incremental_integration": "增量代码集成",
        "aliyun_sync": "阿里云同步",
        "error_auto_fix": "代码报错自动修复",
    }
    
    # 基线模型代码路径
    BASELINE_PATHS = {
        "mtgnn": "code/baseline/mtgnn_model.py",
        "timesnet": "code/baseline/timesnet_model.py",
        "xgboost": "code/baseline/xgboost_model.py",
    }
    
    # 优化模型代码路径
    OPTIMIZED_PATHS = {
        "mtgnn": "code/optimized/mtgnn_model.py",
        "timesnet": "code/optimized/timesnet_model.py",
        "xgboost": "code/optimized/xgboost_model.py",
    }
    
    def __init__(self, env: Optional[Dict[str, str]] = None):
        super().__init__(env)
        self.code_dir = Path(__file__).resolve().parents[2] / "5_code_base"
        self.optimized_dir = self.code_dir / "optimized"
        self.baseline_dir = self.code_dir / "baseline"
        self.aliyun_config = {
            "server_ip": self.env.get("ALIYUN_SERVER_IP", ""),
            "server_user": self.env.get("ALIYUN_SERVER_USER", ""),
            "server_password": self.env.get("ALIYUN_SERVER_PASSWORD", ""),
            "work_dir": self.env.get("ALIYUN_SERVER_WORK_DIR", ""),
        }
    
    def validate_inputs(self, payload: Dict[str, Any]) -> None:
        """验证输入"""
        super().validate_inputs(payload)
        if "innovation_proposal" not in payload and "review_report" not in payload:
            raise ValueError("Missing required field: innovation_proposal or review_report")
    
    def baseline_adaptation(self, baseline_models: List[str] = None) -> Dict[str, Any]:
        """
        基线代码适配
        
        Args:
            baseline_models: 基线模型列表
        
        Returns:
            基线适配结果
        """
        self.log("执行基线代码适配")
        
        if baseline_models is None:
            baseline_models = ["mtgnn", "timesnet", "xgboost"]
        
        adaptation_results = {}
        
        for model_key in baseline_models:
            baseline_path = self.baseline_dir / f"{model_key}_model.py"
            optimized_path = self.optimized_dir / f"{model_key}_model.py"
            
            # 检查基线文件是否存在
            if not baseline_path.exists():
                self.log(f"基线文件不存在：{baseline_path}，创建模板文件")
                self._create_baseline_template(model_key, baseline_path)
            
            # 复制基线文件到优化目录
            if baseline_path.exists():
                optimized_path.parent.mkdir(parents=True, exist_ok=True)
                optimized_path.write_text(baseline_path.read_text(encoding="utf-8"), encoding="utf-8")
                self.log(f"已复制基线文件到优化目录：{optimized_path}")
            
            adaptation_results[model_key] = {
                "baseline_path": str(baseline_path),
                "optimized_path": str(optimized_path),
                "status": "completed" if optimized_path.exists() else "failed",
            }
        
        return {
            "adaptation_results": adaptation_results,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _create_baseline_template(self, model_key: str, path: Path) -> None:
        """创建基线模型模板"""
        templates = {
            "mtgnn": '''"""MTGNN 基线模型"""
import torch
import torch.nn as nn

class MTGNNBaseline(nn.Module):
    def __init__(self, num_nodes, input_dim, output_dim, hidden_dim=32):
        super().__init__()
        self.num_nodes = num_nodes
        self.graph_conv = nn.Linear(input_dim, hidden_dim)
        self.temporal_conv = nn.Conv1d(hidden_dim, hidden_dim, kernel_size=3, padding=1)
        self.output_layer = nn.Linear(hidden_dim, output_dim)
        self.adaptive_adj = nn.Parameter(torch.randn(num_nodes, num_nodes))
    
    def forward(self, x):
        # x: [batch, seq_len, num_nodes, features]
        batch, seq_len, num_nodes, features = x.shape
        x = x.view(batch, seq_len, -1)
        x = torch.relu(self.graph_conv(x))
        x = x.transpose(1, 2)
        x = torch.relu(self.temporal_conv(x))
        x = x.transpose(1, 2)
        x = self.output_layer(x[:, -1, :])
        return x
''',
            "timesnet": '''"""TimesNet 基线模型"""
import torch
import torch.nn as nn
import torch.nn.functional as F

class TimesNetBaseline(nn.Module):
    def __init__(self, input_dim, output_dim, top_k=5, num_freqs=3):
        super().__init__()
        self.top_k = top_k
        self.num_freqs = num_freqs
        self.fft_layer = nn.Linear(input_dim, input_dim * 2)
        self.conv2d = nn.Conv2d(1, 4, kernel_size=(3, 3), padding=(1, 1))
        self.output_layer = nn.Linear(input_dim, output_dim)
    
    def forward(self, x):
        # x: [batch, seq_len, features]
        batch, seq_len, features = x.shape
        x_fft = torch.fft.rfft(x, dim=1)
        x_freq = torch.abs(x_fft)
        top_freqs = torch.topk(x_freq.mean(dim=-1), self.top_k, dim=1)
        x = x_fft[:, :self.top_k, :]
        x = torch.abs(x)
        x = x.view(batch, -1)
        x = self.output_layer(x)
        return x
''',
            "xgboost": '''"""XGBoost 基线模型"""
import numpy as np
try:
    import xgboost as xgb
except ImportError:
    xgb = None

class XGBoostBaseline:
    def __init__(self, max_depth=4, n_estimators=100, learning_rate=0.1):
        self.max_depth = max_depth
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.model = None
    
    def fit(self, X, y):
        if xgb is None:
            raise ImportError("xgboost not installed")
        self.model = xgb.XGBRegressor(
            max_depth=self.max_depth,
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            random_state=42
        )
        self.model.fit(X, y)
        return self
    
    def predict(self, X):
        if self.model is None:
            raise ValueError("Model not fitted")
        return self.model.predict(X)
    
    def score(self, X, y):
        from sklearn.metrics import r2_score
        return r2_score(y, self.predict(X))
''',
        }
        
        path.parent.mkdir(parents=True, exist_ok=True)
        template = templates.get(model_key, f'"""{model_key.upper()} 基线模型模板"""')
        path.write_text(template, encoding="utf-8")
    
    def incremental_coding(
        self,
        innovation_proposal: str,
        review_report: str,
        target_model: str,
    ) -> Dict[str, Any]:
        """
        增量编码 - 使用 qwen3.5-plus 生成代码
        
        Args:
            innovation_proposal: 创新点提案
            review_report: 评审报告
            target_model: 目标模型（mtgnn/timesnet/xgboost）
        
        Returns:
            增量编码结果
        """
        self.log(f"对 {target_model} 执行增量编码")
        
        system_prompt = """你是 Aider 代码生成专家，请根据创新点提案生成可执行的 Python 代码修改方案。

输出格式要求：
## 代码修改方案

### 修改文件：[文件路径]
```python
# 原始代码
# ...

# 修改后代码
# ...
```

### 修改说明
- 修改位置：[具体行号或函数]
- 修改内容：[具体修改了什么]
- 修改原因：[为什么这样修改]

请确保代码可执行、符合 Python 规范，并适配时序预测任务。"""
        
        user_prompt = f"""创新点提案:
{innovation_proposal[:2000]}

评审报告:
{review_report[:2000]}

目标模型：{target_model}

请生成针对 {target_model} 的代码修改方案。"""
        
        response, model_used = self.llm_client.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model="qwen3.5-plus",  # 代码生成使用 qwen3.5-plus
            stage="code_implementation",
        )
        
        self.log(f"增量编码完成，使用模型：{model_used}")
        
        # 解析代码修改
        code_changes = self._parse_code_changes(response, target_model)
        
        return {
            "coding_response": response,
            "code_changes": code_changes,
            "model_used": model_used,
            "target_model": target_model,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _parse_code_changes(self, response: str, target_model: str) -> List[Dict[str, Any]]:
        """解析代码修改内容"""
        changes = []
        
        # 提取代码块
        code_pattern = r'```python\s*(.*?)\s*```'
        code_blocks = re.findall(code_pattern, response, re.DOTALL)
        
        for i, code in enumerate(code_blocks):
            change = {
                "file": f"code/optimized/{target_model}_model.py",
                "code": code,
                "change_type": "modify" if i > 0 else "add",
                "description": f"代码块 {i + 1}",
            }
            changes.append(change)
        
        return changes
    
    def apply_code_changes(
        self,
        code_changes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        应用代码修改
        
        Args:
            code_changes: 代码修改列表
        
        Returns:
            应用结果
        """
        self.log("应用代码修改")
        
        applied = []
        failed = []
        
        for change in code_changes:
            file_path = Path(__file__).resolve().parents[2] / change["file"]
            
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                if change["change_type"] == "add":
                    # 新增文件
                    file_path.write_text(change["code"], encoding="utf-8")
                    self.log(f"已创建文件：{file_path}")
                else:
                    # 修改文件 - 追加内容
                    existing = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
                    file_path.write_text(existing + "\n\n" + change["code"], encoding="utf-8")
                    self.log(f"已修改文件：{file_path}")
                
                applied.append({
                    "file": change["file"],
                    "status": "success",
                })
                
            except Exception as e:
                failed.append({
                    "file": change["file"],
                    "error": str(e),
                })
        
        return {
            "applied": applied,
            "failed": failed,
            "timestamp": datetime.now().isoformat(),
        }
    
    def auto_fix_errors(self, code_path: str, error_message: str) -> Dict[str, Any]:
        """
        报错自动修复
        
        Args:
            code_path: 代码文件路径
            error_message: 错误信息
        
        Returns:
            修复结果
        """
        self.log(f"自动修复错误：{code_path}")
        
        code_file = Path(__file__).resolve().parents[2] / code_path
        if not code_file.exists():
            return {"status": "error", "message": f"File not found: {code_path}"}
        
        code_content = code_file.read_text(encoding="utf-8")
        
        system_prompt = """你是代码调试专家，请分析错误信息并生成修复方案。

输出格式要求：
## 错误分析
- 错误类型：[错误分类]
- 错误原因：[详细分析]

## 修复方案
```python
# 修复后的代码
```

## 修复说明
- 修改内容：[具体修改]
- 修复原理：[为什么这样修复]"""
        
        user_prompt = f"""代码内容:
{code_content[:3000]}

错误信息:
{error_message}

请分析错误并生成修复方案。"""
        
        response, model_used = self.llm_client.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model="qwen3.5-plus",
            stage="code_implementation",
        )
        
        self.log(f"错误修复分析完成，使用模型：{model_used}")
        
        # 提取修复后的代码
        code_pattern = r'```python\s*(.*?)\s*```'
        match = re.search(code_pattern, response, re.DOTALL)
        
        if match:
            fixed_code = match.group(1)
            code_file.write_text(fixed_code, encoding="utf-8")
            return {
                "status": "fixed",
                "fixed_code_path": code_path,
                "model_used": model_used,
            }
        
        return {
            "status": "analyzed",
            "analysis": response,
            "model_used": model_used,
        }
    
    def minimal_validation(self, code_path: str, test_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        最小化验证
        
        Args:
            code_path: 代码文件路径
            test_data: 测试数据
        
        Returns:
            验证结果
        """
        self.log(f"执行最小化验证：{code_path}")
        
        # 尝试导入和运行代码
        validation_result = {
            "import_test": False,
            "syntax_test": False,
            "execution_test": False,
            "errors": [],
        }
        
        code_file = Path(__file__).resolve().parents[2] / code_path
        
        if not code_file.exists():
            validation_result["errors"].append(f"File not found: {code_path}")
            return validation_result
        
        # 语法检查
        try:
            code_content = code_file.read_text(encoding="utf-8")
            compile(code_content, code_file, "exec")
            validation_result["syntax_test"] = True
        except SyntaxError as e:
            validation_result["errors"].append(f"Syntax error: {e}")
        
        # 导入测试
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("test_module", code_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            validation_result["import_test"] = True
        except Exception as e:
            validation_result["errors"].append(f"Import error: {e}")
        
        return {
            **validation_result,
            "timestamp": datetime.now().isoformat(),
        }
    
    def sync_to_aliyun(self, local_paths: List[str]) -> Dict[str, Any]:
        """
        阿里云同步
        
        Args:
            local_paths: 本地文件路径列表
        
        Returns:
            同步结果
        """
        self.log("执行阿里云同步")
        
        if not self.aliyun_config["server_ip"]:
            return {"status": "skipped", "reason": "No Aliyun config"}
        
        synced = []
        failed = []
        
        for local_path in local_paths:
            local_file = Path(__file__).resolve().parents[2] / local_path
            
            if not local_file.exists():
                failed.append({"path": local_path, "error": "File not found"})
                continue
            
            try:
                # 使用 scp 命令同步文件
                remote_path = f"{self.aliyun_config['server_user']}@{self.aliyun_config['server_ip']}:{self.aliyun_config['work_dir']}/{local_path}"
                
                # 注意：实际使用中需要配置 SSH 密钥
                cmd = [
                    "scp",
                    str(local_file),
                    remote_path,
                ]
                
                # 这里仅记录，不实际执行（需要密码或密钥）
                self.log(f"准备同步：{local_path} -> {remote_path}")
                
                synced.append({
                    "path": local_path,
                    "remote_path": remote_path,
                    "status": "pending",  # 实际同步需要 SSH 配置
                })
                
            except Exception as e:
                failed.append({"path": local_path, "error": str(e)})
        
        return {
            "synced": synced,
            "failed": failed,
            "timestamp": datetime.now().isoformat(),
        }
    
    def formula_code_mapping(self, formulas: List[str], code_context: str) -> Dict[str, Any]:
        """
        公式↔代码双向映射
        
        Args:
            formulas: 数学公式列表
            code_context: 代码上下文
        
        Returns:
            映射结果
        """
        self.log("执行公式 - 代码映射")
        
        system_prompt = """你是公式 - 代码映射专家，请将数学公式转换为可执行的 Python 代码。

输出格式要求：
## 公式解析
- 公式含义：[解释公式的数学含义]
- 变量说明：[列出所有变量]

## 代码实现
```python
import numpy as np

def formula_implementation(...):
    # Formula implementation in Python
    ...
```

## 使用示例
```python
# 示例调用
result = formula_implementation(...)
```"""
        
        user_prompt = f"""数学公式:
{chr(10).join(formulas)}

代码上下文:
{code_context[:2000]}

请将公式转换为 Python 代码实现。"""
        
        response, model_used = self.llm_client.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model="qwen3.5-plus",
            stage="code_implementation",
        )
        
        self.log(f"公式 - 代码映射完成，使用模型：{model_used}")
        
        return {
            "mapping_result": response,
            "model_used": model_used,
            "timestamp": datetime.now().isoformat(),
        }
    
    def save_implementation(self, results: Dict[str, Any]) -> Path:
        """保存实现结果"""
        output_dir = Path(__file__).resolve().parents[2] / "8_knowledge_asset" / "code_implementation"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存 JSON 格式
        json_path = output_dir / f"implementation_{timestamp}.json"
        json_path.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        # 保存 Markdown 格式
        md_path = output_dir / f"implementation_{timestamp}.md"
        md_content = f"""# 代码实现报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**使用模型**: {results.get('model_used', 'qwen3.5-plus')}

---

## 基线适配结果
{json.dumps(results.get('baseline_adaptation', {}), indent=2, ensure_ascii=False)}

---

## 增量编码结果
{results.get('incremental_coding', {}).get('coding_response', '暂无数据')}

---

## 代码修改应用
{json.dumps(results.get('code_changes_applied', {}), indent=2, ensure_ascii=False)}

---

## 验证结果
{json.dumps(results.get('validation', {}), indent=2, ensure_ascii=False)}
"""
        md_path.write_text(md_content, encoding="utf-8")
        
        self.log(f"实现结果已保存：{md_path}")
        
        return md_path
    
    def run(self, payload: Dict[str, Any]) -> AgentIO:
        """
        执行代码实现
        
        Args:
            payload: 包含 innovation_proposal, review_report 等
        
        Returns:
            AgentIO 包含实现结果
        """
        self.validate_inputs(payload)
        
        innovation_proposal = payload.get("innovation_proposal", "")
        review_report = payload.get("review_report", "")
        target_models = payload.get("target_models", ["mtgnn", "timesnet", "xgboost"])
        
        self.log("开始代码实现")
        
        results = {
            "baseline_adaptation": {},
            "incremental_coding": {},
            "code_changes_applied": {},
            "validation": {},
            "execution_log": [],
        }
        
        # 1. 基线代码适配
        results["baseline_adaptation"] = self.baseline_adaptation(target_models)
        
        # 2. 增量编码（对每个目标模型）
        for model in target_models:
            coding_result = self.incremental_coding(
                innovation_proposal,
                review_report,
                model,
            )
            results["incremental_coding"][model] = coding_result
            
            # 3. 应用代码修改
            if coding_result.get("code_changes"):
                apply_result = self.apply_code_changes(coding_result["code_changes"])
                results["code_changes_applied"][model] = apply_result
                
                # 4. 最小化验证
                for change in coding_result["code_changes"]:
                    validation = self.minimal_validation(change["file"])
                    results["validation"][change["file"]] = validation
        
        results["execution_log"] = self.get_execution_log()
        
        # 保存结果
        implementation_path = self.save_implementation(results)
        
        # 保存调用日志
        log_dir = Path(__file__).resolve().parents[2] / "7_monitor_system" / "system_log"
        self.llm_client.save_call_log(log_dir / f"code_implementation_call_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        result = {
            "status": "completed",
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "implementation_path": str(implementation_path),
            "model_used": "qwen3.5-plus",
            "execution_log": self.get_execution_log(),
        }
        
        return AgentIO(inputs=payload, outputs=result)