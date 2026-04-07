"""Distributed setup helper — provisions AWS resources for ARISE."""

from __future__ import annotations

import json

import boto3

from arise.config import ARISEConfig


def _get_account_id(session: boto3.Session) -> str:
    sts = session.client("sts")
    return sts.get_caller_identity()["Account"]


def setup_distributed(
    region: str,
    bucket_name: str | None = None,
    queue_name: str | None = None,
    profile: str | None = None,
) -> ARISEConfig:
    """Create S3 bucket + SQS queue (with DLQ) for distributed ARISE.

    Returns an ARISEConfig populated with the created resource identifiers.
    """
    session = boto3.Session(region_name=region, profile_name=profile)
    account_id = _get_account_id(session)

    if bucket_name is None:
        bucket_name = f"arise-skills-{account_id}"
    if queue_name is None:
        queue_name = f"arise-trajectories-{account_id}"

    s3 = session.client("s3")
    sqs = session.client("sqs")

    # --- S3 bucket ---
    create_kwargs: dict = {"Bucket": bucket_name}
    if region != "us-east-1":
        create_kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}
    s3.create_bucket(**create_kwargs)
    s3.put_bucket_versioning(
        Bucket=bucket_name,
        VersioningConfiguration={"Status": "Enabled"},
    )
    bucket_arn = f"arn:aws:s3:::{bucket_name}"
    print(f"Created S3 bucket: {bucket_arn}")

    # --- SQS dead-letter queue ---
    dlq_name = f"{queue_name}-dlq"
    dlq_resp = sqs.create_queue(QueueName=dlq_name)
    dlq_url = dlq_resp["QueueUrl"]
    dlq_attrs = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=["QueueArn"])
    dlq_arn = dlq_attrs["Attributes"]["QueueArn"]
    print(f"Created SQS DLQ:   {dlq_arn}")

    # --- SQS main queue ---
    redrive_policy = json.dumps({"deadLetterTargetArn": dlq_arn, "maxReceiveCount": "5"})
    queue_resp = sqs.create_queue(
        QueueName=queue_name,
        Attributes={"RedrivePolicy": redrive_policy},
    )
    queue_url = queue_resp["QueueUrl"]
    queue_attrs = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["QueueArn"])
    queue_arn = queue_attrs["Attributes"]["QueueArn"]
    print(f"Created SQS queue: {queue_arn}")

    return ARISEConfig(
        s3_bucket=bucket_name,
        sqs_queue_url=queue_url,
        aws_region=region,
    )


def destroy_distributed(config: ARISEConfig) -> None:
    """Delete S3 bucket and SQS queues created by setup_distributed."""
    session = boto3.Session(region_name=config.aws_region)
    s3 = session.resource("s3")
    sqs = session.client("sqs")

    # --- Delete all objects then the bucket ---
    if config.s3_bucket:
        bucket = s3.Bucket(config.s3_bucket)
        bucket.object_versions.all().delete()
        bucket.delete()
        print(f"Deleted S3 bucket: {config.s3_bucket}")

    # --- Delete SQS queues ---
    if config.sqs_queue_url:
        # Derive DLQ URL from main queue URL
        attrs = sqs.get_queue_attributes(
            QueueUrl=config.sqs_queue_url, AttributeNames=["RedrivePolicy"]
        )
        redrive = json.loads(attrs["Attributes"].get("RedrivePolicy", "{}"))
        dlq_arn = redrive.get("deadLetterTargetArn")
        if dlq_arn:
            try:
                dlq_resp = sqs.get_queue_url(QueueName=dlq_arn.split(":")[-1])
                sqs.delete_queue(QueueUrl=dlq_resp["QueueUrl"])
                print(f"Deleted SQS DLQ:   {dlq_arn}")
            except Exception:
                pass

        sqs.delete_queue(QueueUrl=config.sqs_queue_url)
        print(f"Deleted SQS queue: {config.sqs_queue_url}")
