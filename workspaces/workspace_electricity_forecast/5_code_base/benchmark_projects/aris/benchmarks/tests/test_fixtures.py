"""Tests for benchmarks/acmecorp/fixtures.py"""

import os

import pytest

from benchmarks.acmecorp.fixtures import AcmeCorpEnv, generate
from benchmarks.acmecorp.logs import SERVICES


# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def env_seed42():
    env = generate(42)
    yield env
    env.cleanup()


@pytest.fixture(scope="module")
def env_seed42_b():
    """A second independent call with seed=42 for determinism checks."""
    env = generate(42)
    yield env
    env.cleanup()


@pytest.fixture(scope="module")
def env_seed99():
    env = generate(99)
    yield env
    env.cleanup()


# ── Basic shape ───────────────────────────────────────────────────────────────

class TestGenerateReturnsPopulatedEnv:
    def test_returns_acmecorp_env(self, env_seed42):
        assert isinstance(env_seed42, AcmeCorpEnv)

    def test_logs_is_nonempty_list(self, env_seed42):
        assert isinstance(env_seed42.logs, list)
        assert len(env_seed42.logs) > 0

    def test_logs_default_count(self, env_seed42):
        assert len(env_seed42.logs) == 500

    def test_log_file_path_is_str(self, env_seed42):
        assert isinstance(env_seed42.log_file_path, str)

    def test_metrics_data_is_dict(self, env_seed42):
        assert isinstance(env_seed42.metrics_data, dict)

    def test_metrics_data_has_services(self, env_seed42):
        for service in SERVICES:
            assert service in env_seed42.metrics_data

    def test_metrics_port_stored(self, env_seed42):
        assert env_seed42.metrics_port == 18080

    def test_configs_is_dict_with_multiple_files(self, env_seed42):
        assert isinstance(env_seed42.configs, dict)
        assert len(env_seed42.configs) >= 2

    def test_config_data_is_dict(self, env_seed42):
        assert isinstance(env_seed42.config_data, dict)

    def test_config_data_keys_match_configs(self, env_seed42):
        assert set(env_seed42.config_data.keys()) == set(env_seed42.configs.keys())

    def test_ground_truth_is_dict(self, env_seed42):
        assert isinstance(env_seed42.ground_truth, dict)


# ── ground_truth keys ─────────────────────────────────────────────────────────

class TestGroundTruthKeys:
    EXPECTED_KEYS = {
        "error_counts",
        "errors_by_hour",
        "total_errors",
        "services",
        "config_services",
        "config_replicas",
        "metrics",
    }

    def test_has_all_expected_keys(self, env_seed42):
        assert self.EXPECTED_KEYS.issubset(env_seed42.ground_truth.keys())

    def test_error_counts_is_dict(self, env_seed42):
        assert isinstance(env_seed42.ground_truth["error_counts"], dict)

    def test_errors_by_hour_is_dict(self, env_seed42):
        assert isinstance(env_seed42.ground_truth["errors_by_hour"], dict)

    def test_total_errors_is_int(self, env_seed42):
        assert isinstance(env_seed42.ground_truth["total_errors"], int)

    def test_total_errors_matches_error_counts_sum(self, env_seed42):
        gt = env_seed42.ground_truth
        assert gt["total_errors"] == sum(gt["error_counts"].values())

    def test_services_is_list(self, env_seed42):
        assert isinstance(env_seed42.ground_truth["services"], list)

    def test_services_matches_logs_services(self, env_seed42):
        assert set(env_seed42.ground_truth["services"]) == set(SERVICES)

    def test_config_services_is_list(self, env_seed42):
        assert isinstance(env_seed42.ground_truth["config_services"], list)

    def test_config_replicas_is_dict(self, env_seed42):
        assert isinstance(env_seed42.ground_truth["config_replicas"], dict)

    def test_config_replicas_values_are_ints(self, env_seed42):
        for svc, replicas in env_seed42.ground_truth["config_replicas"].items():
            assert isinstance(replicas, int), f"replicas for {svc!r} should be int, got {replicas!r}"

    def test_metrics_in_ground_truth_matches_metrics_data(self, env_seed42):
        assert env_seed42.ground_truth["metrics"] == env_seed42.metrics_data


# ── Log file on disk ──────────────────────────────────────────────────────────

class TestLogFile:
    def test_log_file_exists(self, env_seed42):
        assert os.path.exists(env_seed42.log_file_path)

    def test_log_file_is_a_file(self, env_seed42):
        assert os.path.isfile(env_seed42.log_file_path)

    def test_log_file_contains_logs(self, env_seed42):
        with open(env_seed42.log_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        lines = [l for l in content.splitlines() if l.strip()]
        assert len(lines) == len(env_seed42.logs)

    def test_log_file_content_matches_logs(self, env_seed42):
        with open(env_seed42.log_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        lines = [l for l in content.splitlines() if l.strip()]
        assert lines == env_seed42.logs


# ── Config files on disk ──────────────────────────────────────────────────────

class TestConfigFiles:
    def test_configs_dir_exists(self, env_seed42):
        configs_dir = os.path.join(env_seed42._tmpdir, "configs")
        assert os.path.isdir(configs_dir)

    def test_config_files_written_to_disk(self, env_seed42):
        configs_dir = os.path.join(env_seed42._tmpdir, "configs")
        written = set(os.listdir(configs_dir))
        assert written == set(env_seed42.configs.keys())

    def test_config_file_content_matches(self, env_seed42):
        configs_dir = os.path.join(env_seed42._tmpdir, "configs")
        for filename, text in env_seed42.configs.items():
            path = os.path.join(configs_dir, filename)
            with open(path, "r", encoding="utf-8") as f:
                disk_content = f.read()
            assert disk_content == text


# ── config_data matches parsed configs ───────────────────────────────────────

class TestConfigData:
    def test_config_data_matches_parsed_configs(self, env_seed42):
        from benchmarks.acmecorp.config import parse_acmeconf
        for filename, text in env_seed42.configs.items():
            expected = parse_acmeconf(text)
            assert env_seed42.config_data[filename] == expected

    def test_config_data_has_services_key(self, env_seed42):
        for filename, parsed in env_seed42.config_data.items():
            assert "services" in parsed

    def test_config_data_has_includes_key(self, env_seed42):
        for filename, parsed in env_seed42.config_data.items():
            assert "includes" in parsed


# ── Determinism ───────────────────────────────────────────────────────────────

class TestDeterminism:
    def test_logs_are_deterministic(self, env_seed42, env_seed42_b):
        assert env_seed42.logs == env_seed42_b.logs

    def test_metrics_data_is_deterministic(self, env_seed42, env_seed42_b):
        assert env_seed42.metrics_data == env_seed42_b.metrics_data

    def test_configs_are_deterministic(self, env_seed42, env_seed42_b):
        assert env_seed42.configs == env_seed42_b.configs

    def test_ground_truth_is_deterministic(self, env_seed42, env_seed42_b):
        assert env_seed42.ground_truth == env_seed42_b.ground_truth


# ── Different seeds produce different data ────────────────────────────────────

class TestDifferentSeeds:
    def test_logs_differ_across_seeds(self, env_seed42, env_seed99):
        assert env_seed42.logs != env_seed99.logs

    def test_metrics_differ_across_seeds(self, env_seed42, env_seed99):
        assert env_seed42.metrics_data != env_seed99.metrics_data

    def test_configs_differ_across_seeds(self, env_seed42, env_seed99):
        # Config file sets may differ (different services selected)
        assert env_seed42.configs != env_seed99.configs


# ── Custom parameters ─────────────────────────────────────────────────────────

class TestCustomParameters:
    def test_custom_log_count(self):
        env = generate(seed=1, log_count=100)
        try:
            assert len(env.logs) == 100
        finally:
            env.cleanup()

    def test_custom_metrics_port_stored(self):
        env = generate(seed=1, metrics_port=19999)
        try:
            assert env.metrics_port == 19999
        finally:
            env.cleanup()


# ── cleanup() removes temp files ──────────────────────────────────────────────

class TestCleanup:
    def test_cleanup_removes_tmpdir(self):
        env = generate(seed=7)
        tmpdir = env._tmpdir
        assert os.path.exists(tmpdir)
        env.cleanup()
        assert not os.path.exists(tmpdir)

    def test_cleanup_removes_log_file(self):
        env = generate(seed=8)
        log_path = env.log_file_path
        assert os.path.exists(log_path)
        env.cleanup()
        assert not os.path.exists(log_path)

    def test_cleanup_idempotent(self):
        """Calling cleanup() twice should not raise."""
        env = generate(seed=9)
        env.cleanup()
        env.cleanup()  # second call should not raise
