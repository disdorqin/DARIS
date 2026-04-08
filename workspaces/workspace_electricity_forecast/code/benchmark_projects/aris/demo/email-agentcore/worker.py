"""ARISE Evolution Worker — runs as Lambda or standalone process.

Consumes trajectories from SQS, runs evolution when triggered,
promotes new skills to S3.
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("arise-worker")


def get_worker():
    from arise import ARISEConfig
    from arise.worker import ARISEWorker

    config = ARISEConfig(
        model="bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0",
        s3_bucket=os.environ.get("ARISE_SKILL_BUCKET", "arise-skills-b25e98d0f505"),
        sqs_queue_url=os.environ.get("ARISE_QUEUE_URL",
            "https://sqs.us-west-2.amazonaws.com/436776987862/arise-trajectories-dec74cb26f28"),
        aws_region=os.environ.get("ARISE_AWS_REGION", os.environ.get("AWS_REGION", "us-west-2")),
        failure_threshold=3,
        max_evolutions_per_hour=5,
        sandbox_timeout=60,
        verbose=True,
        allowed_imports=[
            "imaplib", "ssl",
            "email", "email.header", "email.utils", "email.message",
            "email.policy", "email.parser",
            "json", "re", "datetime", "html", "base64",
            "collections", "os",
        ],
    )
    return ARISEWorker(config=config)


# Lambda handler — triggered by SQS
def lambda_handler(event, context):
    from arise.stores.sqs import deserialize_trajectory

    worker = get_worker()
    trajectories = [
        deserialize_trajectory(record["body"])
        for record in event["Records"]
    ]
    logger.info(f"Processing {len(trajectories)} trajectories")
    worker.process_trajectories(trajectories)
    return {"statusCode": 200, "body": f"Processed {len(trajectories)} trajectories"}


# Standalone mode — run forever
if __name__ == "__main__":
    logger.info("Starting ARISE worker (standalone mode)")
    worker = get_worker()
    worker.run_forever(poll_interval=5)
