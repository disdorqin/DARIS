from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from arise.config import ARISEConfig
from arise.skills.forge import SkillForge
from arise.skills.sandbox import Sandbox
from arise.skills.triggers import EvolutionTrigger
from arise.stores.s3 import S3SkillStoreWriter
from arise.stores.sqs import deserialize_trajectory
from arise.types import Trajectory


class ARISEWorker:
    """Background worker that consumes trajectories from SQS and runs evolution.

    Designed for ECS/EC2 (run_forever) or Lambda (run_once).
    """

    def __init__(
        self,
        config: ARISEConfig,
        skill_store: S3SkillStoreWriter | None = None,
        sandbox: Sandbox | None = None,
        sqs_client: Any | None = None,
        s3_client: Any | None = None,
        max_buffer_size: int = 100,
    ):
        self.config = config

        self._skill_store = skill_store or S3SkillStoreWriter(
            bucket=config.s3_bucket or "",
            prefix=config.s3_prefix,
            region=config.aws_region,
            s3_client=s3_client,
        )
        self._sandbox = sandbox or Sandbox(
            backend=config.sandbox_backend,
            timeout=config.sandbox_timeout,
        )
        registry = None
        if config.registry_bucket:
            from arise.registry import SkillRegistry
            registry = SkillRegistry(
                bucket=config.registry_bucket,
                prefix=config.registry_prefix,
                region=config.aws_region,
            )
        llm_router = None
        if config.model_routes:
            from arise.llm_router import LLMRouter
            llm_router = LLMRouter(
                routes=config.model_routes,
                default=config.model,
                auto_select=config.auto_select_model,
            )
        self._forge = SkillForge(
            model=config.model,
            sandbox=self._sandbox,
            max_retries=config.max_refinement_attempts,
            allowed_imports=config.allowed_imports,
            registry=registry,
            llm_router=llm_router,
        )
        self._trigger = EvolutionTrigger(config)

        self._trajectory_buffer: list[Trajectory] = []
        self._max_buffer_size = max_buffer_size

        if sqs_client is not None:
            self._sqs = sqs_client
        elif config.sqs_queue_url:
            import boto3
            self._sqs = boto3.client("sqs", region_name=config.aws_region)
        else:
            self._sqs = None

    def run_forever(self, poll_interval: int = 5) -> None:
        """Long-running loop for ECS/EC2 deployment."""
        if self.config.verbose:
            print("[ARISE Worker] Starting long-poll loop...")
        while True:
            try:
                processed = self.run_once()
                if not processed:
                    time.sleep(poll_interval)
            except KeyboardInterrupt:
                if self.config.verbose:
                    print("[ARISE Worker] Shutting down.")
                break
            except Exception as e:
                print(f"[ARISE Worker] Error: {e}", file=sys.stderr)
                time.sleep(poll_interval)

    def run_once(self) -> int:
        """Poll SQS, buffer trajectories, maybe evolve. Returns count of messages processed."""
        if self._sqs is None or not self.config.sqs_queue_url:
            return 0

        resp = self._sqs.receive_message(
            QueueUrl=self.config.sqs_queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=0,
        )

        messages = resp.get("Messages", [])
        for msg in messages:
            try:
                trajectory = deserialize_trajectory(msg["Body"])
                self._trajectory_buffer.append(trajectory)
                if len(self._trajectory_buffer) > self._max_buffer_size:
                    self._trajectory_buffer = self._trajectory_buffer[-self._max_buffer_size:]
            except Exception as e:
                body_preview = msg.get("Body", "")[:200]
                print(f"[ARISE Worker] Failed to parse message: {e} | body: {body_preview}", file=sys.stderr)

            # Always delete — prevents poison messages from blocking the queue.
            # Parse failures are logged above for debugging.
            self._sqs.delete_message(
                QueueUrl=self.config.sqs_queue_url,
                ReceiptHandle=msg["ReceiptHandle"],
            )

        # Check evolution trigger
        if self._trajectory_buffer and self._trigger.should_evolve(
            self._trajectory_buffer, self._skill_store
        ):
            if self.config.verbose:
                print(f"[ARISE Worker] Evolution triggered with {len(self._trajectory_buffer)} trajectories")
            self._evolve()

        return len(messages)

    def process_trajectories(self, trajectories: list[Trajectory]) -> None:
        """Directly process trajectories (for Lambda handler without SQS polling)."""
        self._trajectory_buffer.extend(trajectories)
        if len(self._trajectory_buffer) > self._max_buffer_size:
            self._trajectory_buffer = self._trajectory_buffer[-self._max_buffer_size:]

        if self._trigger.should_evolve(self._trajectory_buffer, self._skill_store):
            if self.config.verbose:
                print(f"[ARISE Worker] Evolution triggered with {len(self._trajectory_buffer)} trajectories")
            self._evolve()

    def _synthesize_gap(self, gap, failures):
        """Synthesize and validate a single gap. Returns (gap, skill, success) or None."""
        try:
            skill = self._forge.synthesize(gap, self._skill_store)
            result = self._sandbox.test_skill(skill)
            if result.success:
                adv_passed, adv_feedback = self._forge.adversarial_validate(skill)
                if not adv_passed:
                    skill = self._forge.refine(skill, adv_feedback)
                    result = self._sandbox.test_skill(skill)
                    if not result.success:
                        return (gap, skill, False)
                return (gap, skill, True)
            return (gap, skill, False)
        except Exception as e:
            if self.config.verbose:
                print(f"[ARISE Worker] Failed: {gap.suggested_name}: {e}")
            return None

    def _evolve(self) -> None:
        """Run evolution cycle against S3 skill store."""
        failures = [t for t in self._trajectory_buffer if t.reward < 0.5]
        if not failures:
            return

        gaps = self._forge.detect_gaps(failures, self._skill_store)
        if self.config.verbose:
            print(f"[ARISE Worker] Found {len(gaps)} capability gaps.")

        active_names = {s.name for s in self._skill_store.get_active_skills()}
        gaps = [g for g in gaps if g.suggested_name not in active_names]

        # Enforce max_library_size capacity
        active_count = len(self._skill_store.get_active_skills())
        remaining_capacity = self.config.max_library_size - active_count
        if remaining_capacity <= 0:
            if self.config.verbose:
                print("[ARISE Worker] Library at max capacity.")
            self._trajectory_buffer.clear()
            return
        gaps = gaps[:remaining_capacity]

        if gaps:
            if self.config.verbose:
                print(f"[ARISE Worker] Synthesizing {len(gaps)} tools in parallel (max_workers=3)...")

            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(self._synthesize_gap, gap, failures): gap
                    for gap in gaps
                }
                for future in as_completed(futures):
                    result = future.result()
                    if result is None:
                        continue
                    gap, skill, success = result
                    if success:
                        self._skill_store.add(skill)
                        self._skill_store.promote(skill.id)
                        if self.config.verbose:
                            print(f"[ARISE Worker] Skill '{skill.name}' promoted to S3!")
                    else:
                        self._skill_store.add(skill)
                        if self.config.verbose:
                            print(f"[ARISE Worker] Skill '{skill.name}' added (testing).")

        # Clear buffer after evolution
        self._trajectory_buffer.clear()
