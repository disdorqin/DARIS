from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from arise.types import Trajectory
from arise.rewards.builtin import task_success
from arise.llm import llm_call

@dataclass
class FeedbackExample:
    task: str
    outcome: str
    step_count: int
    human_score: float

class LearnedReward:
    """Reward function that learns from human feedback via few-shot prompting."""

    def __init__(self, min_examples: int = 10, persist_path: str | None = None,
                 model: str = "gpt-4o-mini", max_examples: int = 50):
        self.min_examples = min_examples
        self.persist_path = persist_path
        self.model = model
        self.max_examples = max_examples
        self.examples: list[FeedbackExample] = []
        if persist_path:
            self._load()

    def __call__(self, trajectory: Trajectory) -> float:
        if len(self.examples) < self.min_examples:
            return task_success(trajectory)
        return self._llm_score(trajectory)

    def add_feedback(self, trajectory: Trajectory, score: float) -> None:
        self.examples.append(FeedbackExample(
            task=trajectory.task,
            outcome=trajectory.outcome[:500],
            step_count=len(trajectory.steps),
            human_score=score,
        ))
        if len(self.examples) > self.max_examples:
            self.examples = self.examples[-self.max_examples:]
        if self.persist_path:
            self._save()

    def _llm_score(self, trajectory: Trajectory) -> float:
        examples_text = "\n".join(
            f"Task: {e.task[:100]}\nOutcome: {e.outcome[:200]}\nSteps: {e.step_count}\nScore: {e.human_score}"
            for e in self.examples[-10:]
        )
        prompt = f"""Based on these human-scored examples:

{examples_text}

Score this new trajectory (0.0 = failure, 1.0 = perfect):
Task: {trajectory.task[:200]}
Outcome: {trajectory.outcome[:500]}
Steps: {len(trajectory.steps)}

Return ONLY a number between 0.0 and 1.0."""

        try:
            result = llm_call([{"role": "user", "content": prompt}], model=self.model, max_tokens=10)
            score = float(result.strip())
            return max(0.0, min(1.0, score))
        except Exception:
            return task_success(trajectory)

    def _save(self) -> None:
        path = os.path.join(self.persist_path, "feedback.json")
        data = [{"task": e.task, "outcome": e.outcome, "step_count": e.step_count, "human_score": e.human_score}
                for e in self.examples]
        with open(path, "w") as f:
            json.dump(data, f)

    def _load(self) -> None:
        path = os.path.join(self.persist_path, "feedback.json")
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            self.examples = [FeedbackExample(**d) for d in data]
