"""Background agent runner that emits events over WebSocket."""
import asyncio
import json
import os
import time
from datetime import datetime
from typing import Any

from arise import ARISE


class AgentRunner:
    """Wraps ARISE.run() to emit structured events for WebSocket clients.

    Events are persisted to a JSONL file so they survive page reloads.
    """

    def __init__(self, arise: ARISE, agent_id: str, data_dir: str = ""):
        self.arise = arise
        self.agent_id = agent_id
        self._subscribers: list[asyncio.Queue] = []

        # Persistent event log
        self._log_path = ""
        if data_dir:
            log_dir = os.path.join(data_dir, "agents", agent_id)
            os.makedirs(log_dir, exist_ok=True)
            self._log_path = os.path.join(log_dir, "events.jsonl")

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self._subscribers:
            self._subscribers.remove(q)

    def get_history(self, limit: int = 100) -> list[dict]:
        """Load recent events from disk."""
        if not self._log_path or not os.path.exists(self._log_path):
            return []
        events = []
        with open(self._log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return events[-limit:]

    def _emit(self, event: dict):
        event["agent_id"] = self.agent_id
        event["timestamp"] = datetime.now().isoformat()

        # Persist to disk
        if self._log_path:
            with open(self._log_path, "a") as f:
                f.write(json.dumps(event) + "\n")

        # Push to WebSocket subscribers
        for q in self._subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    def run_task(self, task: str) -> str:
        episode = self.arise.stats.get("episodes_run", 0) + 1
        self._emit({"type": "episode_start", "episode": episode, "task": task})

        # Patch forge to emit live synthesis events
        self._patch_forge()

        # Patch evolve to emit evolution lifecycle events
        original_evolve = self.arise.evolve
        def patched_evolve():
            self._emit({"type": "evolution_start", "reason": "failure_streak"})
            original_evolve()
            report = self.arise.last_evolution
            if report:
                self._emit({
                    "type": "evolution_end",
                    "promoted": report.tools_promoted,
                    "rejected": report.tools_rejected,
                    "duration_ms": report.duration_ms,
                })
        self.arise.evolve = patched_evolve

        try:
            result = self.arise.run(task)
        finally:
            self.arise.evolve = original_evolve
            self._unpatch_forge()

        # Get reward from latest trajectory
        reward = 0.0
        if hasattr(self.arise, 'trajectory_store') and self.arise.trajectory_store:
            recent = self.arise.trajectory_store.get_recent(1)
            if recent:
                reward = recent[0].reward

        self._emit({
            "type": "episode_end",
            "episode": episode,
            "reward": reward,
            "status": "ok" if reward >= 0.5 else "fail",
            "skills": len(self.arise.skills),
            "result_preview": result[:200],
        })

        return result

    def _patch_forge(self):
        """Patch the SkillForge to emit events during synthesis."""
        if not self.arise.forge:
            return

        forge = self.arise.forge
        self._original_detect = forge.detect_gaps
        self._original_synthesize = forge.synthesize

        runner = self

        def patched_detect(failures, library):
            runner._emit({"type": "forge_detecting", "failure_count": len(failures)})
            gaps = runner._original_detect(failures, library)
            for gap in gaps:
                runner._emit({
                    "type": "gap_detected",
                    "description": gap.description,
                    "suggested_name": gap.suggested_name,
                })
            return gaps

        def patched_synthesize(gap, library, example_trajectories=None):
            runner._emit({
                "type": "synthesis_start",
                "name": gap.suggested_name,
                "description": gap.description,
            })
            try:
                skill = runner._original_synthesize(gap, library, example_trajectories)
                runner._emit({
                    "type": "skill_promoted",
                    "name": skill.name,
                    "id": skill.id,
                })
                return skill
            except Exception as e:
                runner._emit({
                    "type": "skill_rejected",
                    "name": gap.suggested_name,
                    "reason": str(e)[:200],
                })
                raise

        forge.detect_gaps = patched_detect
        forge.synthesize = patched_synthesize

    def _unpatch_forge(self):
        """Restore original forge methods."""
        if not self.arise.forge:
            return
        if hasattr(self, '_original_detect'):
            self.arise.forge.detect_gaps = self._original_detect
        if hasattr(self, '_original_synthesize'):
            self.arise.forge.synthesize = self._original_synthesize
