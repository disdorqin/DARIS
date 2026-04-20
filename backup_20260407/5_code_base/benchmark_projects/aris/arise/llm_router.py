from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ModelStats:
    attempts: int = 0
    successes: int = 0

    @property
    def success_rate(self) -> float:
        return self.successes / self.attempts if self.attempts > 0 else 0.0


class LLMRouter:
    """Routes LLM calls to different models based on task type."""

    def __init__(
        self,
        routes: dict[str, str] | None = None,
        default: str = "gpt-4o-mini",
        auto_select: bool = False,
    ):
        self._routes = routes or {}
        self._default = default
        self._auto_select = auto_select
        self._stats: dict[str, dict[str, ModelStats]] = {}  # task_type -> model -> stats

    def get_model(self, task_type: str) -> str:
        if self._auto_select:
            best = self._best_model(task_type)
            if best:
                return best
        return self._routes.get(task_type, self._default)

    def record(self, task_type: str, model: str, success: bool) -> None:
        if task_type not in self._stats:
            self._stats[task_type] = {}
        if model not in self._stats[task_type]:
            self._stats[task_type][model] = ModelStats()
        stats = self._stats[task_type][model]
        stats.attempts += 1
        if success:
            stats.successes += 1

    def get_stats(self, task_type: str, model: str) -> dict:
        stats = self._stats.get(task_type, {}).get(model, ModelStats())
        return {
            "attempts": stats.attempts,
            "successes": stats.successes,
            "success_rate": stats.success_rate,
        }

    def _best_model(self, task_type: str) -> str | None:
        """Pick model with highest success rate (minimum 5 attempts)."""
        task_stats = self._stats.get(task_type, {})
        best_model = None
        best_rate = -1.0
        for model, stats in task_stats.items():
            if stats.attempts >= 5 and stats.success_rate > best_rate:
                best_rate = stats.success_rate
                best_model = model
        return best_model
