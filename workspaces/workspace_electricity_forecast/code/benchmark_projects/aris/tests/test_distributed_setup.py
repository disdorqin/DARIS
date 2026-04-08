"""Tests for arise.distributed — setup and teardown of AWS resources."""

import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arise.config import ARISEConfig
from arise.distributed import setup_distributed, destroy_distributed


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_session(account_id="123456789012"):
    """Return a mock boto3.Session with STS, S3, and SQS clients."""
    session = MagicMock()

    sts = MagicMock()
    sts.get_caller_identity.return_value = {"Account": account_id}

    s3_client = MagicMock()

    sqs = MagicMock()
    sqs.create_queue.side_effect = [
        {"QueueUrl": "https://sqs.us-west-2.amazonaws.com/123456789012/arise-trajectories-123456789012-dlq"},
        {"QueueUrl": "https://sqs.us-west-2.amazonaws.com/123456789012/arise-trajectories-123456789012"},
    ]
    sqs.get_queue_attributes.side_effect = [
        {"Attributes": {"QueueArn": "arn:aws:sqs:us-west-2:123456789012:arise-trajectories-123456789012-dlq"}},
        {"Attributes": {"QueueArn": "arn:aws:sqs:us-west-2:123456789012:arise-trajectories-123456789012"}},
    ]

    def _client(service, **kwargs):
        return {"sts": sts, "s3": s3_client, "sqs": sqs}[service]

    session.client.side_effect = _client
    return session, s3_client, sqs


# ---------------------------------------------------------------------------
# setup_distributed
# ---------------------------------------------------------------------------

@patch("arise.distributed.boto3.Session")
def test_setup_distributed_auto_names(mock_session_cls):
    session, s3, sqs = _make_mock_session()
    mock_session_cls.return_value = session

    config = setup_distributed(region="us-west-2")

    assert config.s3_bucket == "arise-skills-123456789012"
    assert config.aws_region == "us-west-2"
    assert "123456789012" in config.sqs_queue_url

    # Bucket created with LocationConstraint for non-us-east-1
    s3.create_bucket.assert_called_once()
    create_args = s3.create_bucket.call_args
    assert create_args[1]["CreateBucketConfiguration"] == {"LocationConstraint": "us-west-2"}

    # Versioning enabled
    s3.put_bucket_versioning.assert_called_once_with(
        Bucket="arise-skills-123456789012",
        VersioningConfiguration={"Status": "Enabled"},
    )

    # DLQ created first, then main queue
    assert sqs.create_queue.call_count == 2
    dlq_call = sqs.create_queue.call_args_list[0]
    assert dlq_call == call(QueueName="arise-trajectories-123456789012-dlq")

    main_call = sqs.create_queue.call_args_list[1]
    assert main_call[1]["QueueName"] == "arise-trajectories-123456789012"
    redrive = json.loads(main_call[1]["Attributes"]["RedrivePolicy"])
    assert redrive["maxReceiveCount"] == "5"


@patch("arise.distributed.boto3.Session")
def test_setup_distributed_custom_names(mock_session_cls):
    session, s3, sqs = _make_mock_session()
    mock_session_cls.return_value = session

    config = setup_distributed(
        region="us-east-1",
        bucket_name="my-bucket",
        queue_name="my-queue",
    )

    assert config.s3_bucket == "my-bucket"
    s3.create_bucket.assert_called_once_with(Bucket="my-bucket")
    # us-east-1 should NOT include LocationConstraint
    create_args = s3.create_bucket.call_args
    assert "CreateBucketConfiguration" not in create_args[1]


@patch("arise.distributed.boto3.Session")
def test_setup_distributed_passes_profile(mock_session_cls):
    session, _, _ = _make_mock_session()
    mock_session_cls.return_value = session

    setup_distributed(region="eu-west-1", profile="staging")

    mock_session_cls.assert_called_once_with(region_name="eu-west-1", profile_name="staging")


# ---------------------------------------------------------------------------
# destroy_distributed
# ---------------------------------------------------------------------------

@patch("arise.distributed.boto3.Session")
def test_destroy_distributed(mock_session_cls):
    session = MagicMock()
    s3_resource = MagicMock()
    bucket_obj = MagicMock()
    s3_resource.Bucket.return_value = bucket_obj

    sqs = MagicMock()
    sqs.get_queue_attributes.return_value = {
        "Attributes": {
            "RedrivePolicy": json.dumps({
                "deadLetterTargetArn": "arn:aws:sqs:us-west-2:123456789012:my-dlq",
                "maxReceiveCount": "5",
            })
        }
    }
    sqs.get_queue_url.return_value = {"QueueUrl": "https://sqs.us-west-2.amazonaws.com/123456789012/my-dlq"}

    def _client(service, **kwargs):
        return {"sqs": sqs}[service]

    session.client.side_effect = _client
    session.resource.return_value = s3_resource
    mock_session_cls.return_value = session

    config = ARISEConfig(
        s3_bucket="my-bucket",
        sqs_queue_url="https://sqs.us-west-2.amazonaws.com/123456789012/my-queue",
        aws_region="us-west-2",
    )

    destroy_distributed(config)

    # Bucket emptied and deleted
    bucket_obj.object_versions.all().delete.assert_called_once()
    bucket_obj.delete.assert_called_once()

    # DLQ and main queue deleted
    assert sqs.delete_queue.call_count == 2


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

@patch("arise.distributed.boto3.Session")
def test_cli_setup_distributed(mock_session_cls):
    session, s3, sqs = _make_mock_session()
    mock_session_cls.return_value = session

    old_cwd = os.getcwd()
    tmpdir = tempfile.mkdtemp()
    try:
        os.chdir(tmpdir)

        from arise.cli import main
        sys.argv = ["arise", "setup-distributed", "--region", "us-west-2"]
        main()

        config_path = os.path.join(tmpdir, ".arise.json")
        assert os.path.exists(config_path)
        with open(config_path) as f:
            data = json.load(f)
        assert data["s3_bucket"] == "arise-skills-123456789012"
        assert data["aws_region"] == "us-west-2"
    finally:
        os.chdir(old_cwd)


@patch("arise.distributed.boto3.Session")
def test_cli_setup_distributed_destroy(mock_session_cls):
    session = MagicMock()
    s3_resource = MagicMock()
    bucket_obj = MagicMock()
    s3_resource.Bucket.return_value = bucket_obj

    sqs = MagicMock()
    sqs.get_queue_attributes.return_value = {
        "Attributes": {
            "RedrivePolicy": json.dumps({
                "deadLetterTargetArn": "arn:aws:sqs:us-west-2:123456789012:dlq",
                "maxReceiveCount": "5",
            })
        }
    }
    sqs.get_queue_url.return_value = {"QueueUrl": "https://sqs.us-west-2.amazonaws.com/123456789012/dlq"}

    def _client(service, **kwargs):
        return {"sqs": sqs}[service]

    session.client.side_effect = _client
    session.resource.return_value = s3_resource
    mock_session_cls.return_value = session

    old_cwd = os.getcwd()
    tmpdir = tempfile.mkdtemp()
    try:
        os.chdir(tmpdir)

        # Write a fake .arise.json
        with open(".arise.json", "w") as f:
            json.dump({
                "s3_bucket": "my-bucket",
                "sqs_queue_url": "https://sqs.us-west-2.amazonaws.com/123456789012/my-queue",
                "aws_region": "us-west-2",
            }, f)

        from arise.cli import main
        sys.argv = ["arise", "setup-distributed", "--destroy"]
        main()

        assert not os.path.exists(".arise.json")
    finally:
        os.chdir(old_cwd)
