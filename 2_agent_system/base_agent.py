from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict
@dataclass
class AgentIO:
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
class BaseAgent:
    name = "base_agent"
    def validate_inputs(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            raise TypeError("payload must be dict")
    def run(self, payload: Dict[str, Any]) -> AgentIO:
        self.validate_inputs(payload)
        result = {
            "status": "ok",
            "agent": self.name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        return AgentIO(inputs=payload, outputs=result)
