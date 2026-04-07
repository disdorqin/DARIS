from __future__ import annotations

import json
import sys
import threading
from datetime import datetime

from arise.stores.base import TrajectoryReporter
from arise.types import Step, Trajectory


def _serialize_trajectory(trajectory: Trajectory) -> str:
    return json.dumps({
        "task": trajectory.task,
        "steps": [
            {
                "observation": s.observation,
                "reasoning": s.reasoning,
                "action": s.action,
                "action_input": s.action_input,
                "result": s.result,
                "error": s.error,
                "latency_ms": s.latency_ms,
            }
            for s in trajectory.steps
        ],
        "outcome": trajectory.outcome,
        "reward": trajectory.reward,
        "skill_library_version": trajectory.skill_library_version,
        "timestamp": trajectory.timestamp.isoformat(),
        "metadata": trajectory.metadata,
    })


def deserialize_trajectory(body: str) -> Trajectory:
    data = json.loads(body)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object, got {type(data).__name__}")
    if "task" not in data:
        raise ValueError("Missing required field 'task'")

    raw_steps = data.get("steps", [])
    if not isinstance(raw_steps, list):
        raise ValueError(f"'steps' must be a list, got {type(raw_steps).__name__}")

    steps = []
    for s in raw_steps:
        if isinstance(s, dict):
            steps.append(Step(**{k: v for k, v in s.items() if k in Step.__dataclass_fields__}))

    return Trajectory(
        task=str(data["task"]),
        steps=steps,
        outcome=str(data.get("outcome", "")),
        reward=float(data.get("reward", 0.0)),
        skill_library_version=int(data.get("skill_library_version", 0)),
        timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(),
        metadata=data.get("metadata", {}) if isinstance(data.get("metadata"), dict) else {},
    )


class SQSTrajectoryReporter(TrajectoryReporter):
    """Fire-and-forget trajectory reporter via SQS.

    Sends messages in a daemon thread so report() never blocks the agent.
    """

    def __init__(
        self,
        queue_url: str,
        region: str = "us-east-1",
        sqs_client: object | None = None,
    ):
        self._queue_url = queue_url

        if sqs_client is not None:
            self._sqs = sqs_client
        else:
            import boto3
            self._sqs = boto3.client("sqs", region_name=region)

    def report(self, trajectory: Trajectory) -> None:
        """Send trajectory to SQS in a daemon thread. Errors go to stderr."""
        body = _serialize_trajectory(trajectory)
        thread = threading.Thread(target=self._send, args=(body,), daemon=True)
        thread.start()

    def report_sync(self, trajectory: Trajectory) -> None:
        """Synchronous send for testing."""
        body = _serialize_trajectory(trajectory)
        self._send(body)

    def _send(self, body: str) -> None:
        try:
            self._sqs.send_message(QueueUrl=self._queue_url, MessageBody=body)
        except Exception as e:
            print(f"[ARISE] SQS send failed: {e}", file=sys.stderr)
