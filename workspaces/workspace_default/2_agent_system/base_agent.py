from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


@dataclass
class AgentIO:
    """智能体输入输出封装"""
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    base_url: str
    api_key: str
    timeout: int = 120
    temperature: float = 0.2


class LLMClient:
    """多模型调用客户端，支持 fallback 机制"""
    
    # 备选 API 端点配置
    ENDPOINTS = {
        "beijing": {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key_env": "DASHSCOPE_API_KEY",
        },
        "singapore": {
            "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            "api_key_env": "DASHSCOPE_SG_API_KEY",
        },
        "us_virginia": {
            "base_url": "https://dashscope-us.aliyuncs.com/compatible-mode/v1",
            "api_key_env": "DASHSCOPE_US_API_KEY",
        },
    }
    
    # 环节到模型的映射
    MODEL_ROUTING = {
        "literature": "kimi-k2.5",          # 文献阅读/总结
        "innovation": "glm-5",              # 创新点提出
        "innovation_review": "MiniMax-M2.5", # 创新点评审
        "code_implementation": "qwen3.5-plus", # 代码实现
        "experiment_tuning": "qwen3.5-plus",   # 实验调优
        "global_scheduler": "qwen3.5-plus",    # 全局调度
    }
    
    def __init__(self, env: Optional[Dict[str, str]] = None):
        self.env = env or self._load_env()
        self._call_history: List[Dict[str, Any]] = []
    
    @staticmethod
    def _load_env() -> Dict[str, str]:
        """从.env 文件加载环境变量"""
        env = dict(os.environ)
        env_file = Path(__file__).resolve().parents[2] / ".env"
        if env_file.exists():
            for raw in env_file.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip().strip('"').strip("'")
        return env
    
    def get_model_for_stage(self, stage: str) -> str:
        """根据环节获取指定模型"""
        return self.MODEL_ROUTING.get(stage, "qwen3.5-plus")
    
    def _get_available_endpoints(self) -> List[Tuple[str, str]]:
        """获取可用的 API 端点列表"""
        endpoints = []
        for name, config in self.ENDPOINTS.items():
            api_key = self.env.get(config["api_key_env"], "")
            if api_key and not api_key.startswith("你的"):
                endpoints.append((config["base_url"], api_key, name))
        
        # 如果主配置中有 OPENAI_BASE_URLS 和 OPENAI_API_KEYS，也加入
        base_urls = self.env.get("OPENAI_BASE_URLS", "")
        api_keys = self.env.get("OPENAI_API_KEYS", "")
        if base_urls and api_keys:
            urls = [u.strip() for u in base_urls.split(",")]
            keys = [k.strip() for k in api_keys.split(",")]
            for url, key in zip(urls, keys):
                if key and not key.startswith("你的"):
                    endpoints.append((url, key, "custom"))
        
        return endpoints
    
    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        stage: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 120,
    ) -> Tuple[str, str]:
        """
        调用大模型 API
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            model: 指定模型名称，如不指定则根据 stage 自动选择
            stage: 环节名称，用于模型路由
            max_retries: 最大重试次数
            timeout: 超时时间（秒）
        
        Returns:
            (response_text, model_used)
        """
        if model is None:
            model = self.get_model_for_stage(stage) if stage else "qwen3.5-plus"
        
        endpoints = self._get_available_endpoints()
        if not endpoints:
            return self._fallback_response(user_prompt), "local-fallback"
        
        last_error = ""
        for retry in range(max_retries):
            for base_url, api_key, endpoint_name in endpoints:
                try:
                    endpoint = f"{base_url.rstrip('/')}/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    }
                    payload = {
                        "model": model,
                        "temperature": 0.2,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                    }
                    
                    resp = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
                    if resp.status_code >= 400:
                        last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                        continue
                    
                    data = resp.json()
                    text = data["choices"][0]["message"]["content"]
                    
                    # 记录调用历史
                    self._call_history.append({
                        "timestamp": datetime.now().isoformat(),
                        "stage": stage,
                        "model": model,
                        "endpoint": endpoint_name,
                        "status": "success",
                    })
                    
                    return text, model
                    
                except Exception as exc:
                    last_error = str(exc)
                    continue
        
        # 所有尝试都失败，使用本地兜底
        return self._fallback_response(user_prompt, last_error), "local-fallback"
    
    @staticmethod
    def _fallback_response(user_prompt: str, error: str = "") -> str:
        """本地兜底响应生成"""
        hint = ""
        compact = user_prompt.replace("\n", " ")[:260]
        
        if "文献" in user_prompt or "阅读" in user_prompt or "总结" in user_prompt:
            hint = """
【本地文献分析兜底】
1. 研究脉络：图神经网络与时序预测融合是主流方向
2. 常见缺陷：对突发波动鲁棒性不足、物理约束缺失
3. 可利用空白：轻量约束与可解释特征解耦的联合优化
4. 建议关注：MTGNN、TimesNet、XGBoost 在电力负荷预测中的改进
"""
        elif "创新" in user_prompt:
            hint = """
【本地创新点兜底】
创新点 A: 动态图门控 + 自适应窗口，改动 MTGNN 优化分支
创新点 B: 趋势残差解耦 + 物理约束，改动 TimesNet 优化分支
创新点 C: 长窗特征 + 稳健树深调优，改动 XGBoost 优化分支
评估指标：MAE/RMSE/R2 + 稳定性
"""
        elif "评审" in user_prompt or "风险" in user_prompt:
            hint = """
【本地评审兜底】
1. 通过项：创新目标可落地且可量化
2. 风险项：参数过拟合、数据分布漂移、训练时长增加
3. 必须修改项：增加回退机制、限制学习率/深度、保留 baseline 对照
4. 执行建议：先做 demo 验证，再跑三基线全量评测
"""
        else:
            hint = f"【本地兜底】输入：{compact}"
        
        if error:
            hint = f"API 调用失败：{error[:100]}\n\n{hint}"
        
        return hint
    
    def get_call_history(self) -> List[Dict[str, Any]]:
        """获取调用历史"""
        return self._call_history
    
    def save_call_log(self, output_path: Path) -> None:
        """保存调用日志到文件"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(self._call_history, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )


class BaseAgent:
    """智能体基类"""
    
    name = "base_agent"
    description = "基础智能体"
    
    def __init__(self, env: Optional[Dict[str, str]] = None):
        self.env = env or LLMClient._load_env()
        self.llm_client = LLMClient(self.env)
        self._execution_log: List[str] = []
    
    def log(self, message: str) -> None:
        """记录执行日志"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._execution_log.append(f"[{ts}] {message}")
        print(f"[{ts}] {message}", flush=True)
    
    def validate_inputs(self, payload: Dict[str, Any]) -> None:
        """验证输入"""
        if not isinstance(payload, dict):
            raise TypeError("payload must be dict")
    
    def run(self, payload: Dict[str, Any]) -> AgentIO:
        """执行智能体任务"""
        self.validate_inputs(payload)
        result = {
            "status": "ok",
            "agent": self.name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        return AgentIO(inputs=payload, outputs=result)
    
    def get_execution_log(self) -> List[str]:
        """获取执行日志"""
        return self._execution_log
    
    def save_execution_log(self, output_path: Path) -> None:
        """保存执行日志到文件"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            "\n".join(self._execution_log),
            encoding="utf-8"
        )