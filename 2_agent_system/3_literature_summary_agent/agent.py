from __future__ import annotations
import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from base_agent import BaseAgent
class LiteratureSummaryAgent(BaseAgent):
    name = "literature_summary_agent"
