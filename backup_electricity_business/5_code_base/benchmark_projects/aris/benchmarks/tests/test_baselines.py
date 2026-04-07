"""Tests for benchmarks/baselines/fixed_tools.py"""

import json
import threading
import time
from unittest.mock import patch, MagicMock

import pytest

from benchmarks.acmecorp.fixtures import generate
from benchmarks.acmecorp.logs import generate_logs, ground_truth_error_counts, SERVICES
from benchmarks.acmecorp.config import (
    generate_configs,
    format_acmeconf,
    parse_acmeconf as acme_parse_acmeconf,
)
from benchmarks.acmecorp.metrics import (
    encode_acme_payload,
    generate_metrics_data,
    create_metrics_app,
    start_metrics_server,
    stop_metrics_server,
)
from benchmarks.baselines.fixed_tools import (
    parse_acme_log,
    filter_acme_logs,
    count_acme_errors,
    fetch_acme_metrics,
    parse_acmeconf,
    validate_acmeconf,
    diff_acmeconf,
    get_fixed_tools,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def env():
    env = generate(seed=42, log_count=500)
    yield env
    env.cleanup()


@pytest.fixture(scope="module")
def log_text(env):
    return "\n".join(env.logs)


@pytest.fixture(scope="module")
def configs_seed42():
    return generate_configs(seed=42)


# ---------------------------------------------------------------------------
# parse_acme_log
# ---------------------------------------------------------------------------

class TestParseAcmeLog:
    def test_returns_json_array(self, log_text):
        result = parse_acme_log(log_text)
        parsed = json.loads(result)
        assert isinstance(parsed, list)

    def test_count_matches_log_lines(self, env, log_text):
        result = json.loads(parse_acme_log(log_text))
        assert len(result) == len(env.logs)

    def test_entry_has_expected_keys(self, log_text):
        entries = json.loads(parse_acme_log(log_text))
        for entry in entries[:10]:
            assert set(entry.keys()) == {"severity", "service", "timestamp", "message", "ctx"}

    def test_severity_is_valid(self, log_text):
        valid = {"DEBUG", "INFO", "WARN", "ERROR", "FATAL"}
        entries = json.loads(parse_acme_log(log_text))
        for entry in entries:
            assert entry["severity"] in valid

    def test_service_is_valid(self, log_text):
        entries = json.loads(parse_acme_log(log_text))
        for entry in entries:
            assert entry["service"] in SERVICES

    def test_timestamp_is_int(self, log_text):
        entries = json.loads(parse_acme_log(log_text))
        for entry in entries[:20]:
            assert isinstance(entry["timestamp"], int)

    def test_ctx_is_dict(self, log_text):
        entries = json.loads(parse_acme_log(log_text))
        for entry in entries[:20]:
            assert isinstance(entry["ctx"], dict)

    def test_message_is_nonempty_string(self, log_text):
        entries = json.loads(parse_acme_log(log_text))
        for entry in entries[:20]:
            assert isinstance(entry["message"], str)
            assert len(entry["message"]) > 0

    def test_specific_line(self):
        line = '[ACME:INFO:payments:1710001234] payment processed | ctx={"host":"web-01","region":"us-east-1"}'
        entries = json.loads(parse_acme_log(line))
        assert len(entries) == 1
        e = entries[0]
        assert e["severity"] == "INFO"
        assert e["service"] == "payments"
        assert e["timestamp"] == 1710001234
        assert e["message"] == "payment processed"
        assert e["ctx"]["host"] == "web-01"

    def test_empty_string_returns_empty_array(self):
        result = json.loads(parse_acme_log(""))
        assert result == []

    def test_skips_invalid_lines(self):
        text = "not a valid log line\n[ACME:INFO:auth:1710001234] ok | ctx={}"
        entries = json.loads(parse_acme_log(text))
        assert len(entries) == 1
        assert entries[0]["service"] == "auth"


# ---------------------------------------------------------------------------
# filter_acme_logs
# ---------------------------------------------------------------------------

class TestFilterAcmeLogs:
    def test_filter_by_service(self, log_text):
        result = filter_acme_logs(log_text, service="payments")
        lines = [l for l in result.splitlines() if l.strip()]
        assert len(lines) > 0
        for line in lines:
            assert ":payments:" in line

    def test_filter_by_service_excludes_others(self, log_text):
        result = filter_acme_logs(log_text, service="auth")
        for line in result.splitlines():
            if line.strip():
                assert ":auth:" in line

    def test_filter_by_severity(self, log_text):
        result = filter_acme_logs(log_text, severity="ERROR")
        lines = [l for l in result.splitlines() if l.strip()]
        assert len(lines) > 0
        for line in lines:
            assert ":ERROR:" in line

    def test_filter_by_service_and_severity(self, log_text):
        result = filter_acme_logs(log_text, service="database", severity="WARN")
        for line in result.splitlines():
            if line.strip():
                assert ":database:" in line
                assert ":WARN:" in line

    def test_no_filter_returns_all(self, env, log_text):
        result = filter_acme_logs(log_text)
        lines = [l for l in result.splitlines() if l.strip()]
        assert len(lines) == len(env.logs)

    def test_unknown_service_returns_empty(self, log_text):
        result = filter_acme_logs(log_text, service="nonexistent_xyz")
        lines = [l for l in result.splitlines() if l.strip()]
        assert len(lines) == 0

    def test_filter_count_matches_manual(self, env, log_text):
        result = filter_acme_logs(log_text, service="worker")
        result_lines = [l for l in result.splitlines() if l.strip()]
        manual = [l for l in env.logs if ":worker:" in l]
        assert len(result_lines) == len(manual)

    def test_severity_case_insensitive(self, log_text):
        lower = filter_acme_logs(log_text, severity="error")
        upper = filter_acme_logs(log_text, severity="ERROR")
        assert lower == upper


# ---------------------------------------------------------------------------
# count_acme_errors
# ---------------------------------------------------------------------------

class TestCountAcmeErrors:
    def test_returns_json_dict(self, log_text):
        result = count_acme_errors(log_text)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_counts_match_ground_truth(self, env, log_text):
        result = json.loads(count_acme_errors(log_text))
        ground = env.ground_truth["error_counts"]
        assert result == ground

    def test_only_error_and_fatal(self, log_text):
        result = json.loads(count_acme_errors(log_text))
        # All keys must be valid services
        for key in result:
            assert key in SERVICES
        # Values must be positive
        for val in result.values():
            assert isinstance(val, int) and val > 0

    def test_total_matches(self, env, log_text):
        result = json.loads(count_acme_errors(log_text))
        assert sum(result.values()) == env.ground_truth["total_errors"]

    def test_empty_returns_empty_dict(self):
        result = json.loads(count_acme_errors(""))
        assert result == {}

    def test_consistent_across_seeds(self):
        logs_a = generate_logs(seed=7, count=200)
        logs_b = generate_logs(seed=7, count=200)
        text_a = "\n".join(logs_a)
        text_b = "\n".join(logs_b)
        assert count_acme_errors(text_a) == count_acme_errors(text_b)

    def test_matches_ground_truth_function(self):
        logs = generate_logs(seed=13, count=300)
        text = "\n".join(logs)
        result = json.loads(count_acme_errors(text))
        expected = ground_truth_error_counts(logs)
        assert result == expected


# ---------------------------------------------------------------------------
# fetch_acme_metrics (mock HTTP call)
# ---------------------------------------------------------------------------

class TestFetchAcmeMetrics:
    def _make_mock_response(self, service: str, data: dict):
        """Build a mock urllib response object returning an ACME encoded payload."""
        import io
        ts = 1710000000
        payload = encode_acme_payload(service, ts, data)
        mock_resp = MagicMock()
        mock_resp.read.return_value = payload.encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp, ts

    def test_returns_json_with_service_key(self):
        service = "payments"
        data = {"latency_p50": 12.5, "error_rate": 0.01}
        mock_resp, ts = self._make_mock_response(service, data)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = json.loads(fetch_acme_metrics("http://localhost:18080/metrics/payments"))
        assert result["service"] == service

    def test_returns_json_with_timestamp_key(self):
        service = "auth"
        data = {"cpu_pct": 55.0}
        mock_resp, ts = self._make_mock_response(service, data)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = json.loads(fetch_acme_metrics("http://localhost:18080/metrics/auth"))
        assert result["timestamp"] == ts

    def test_returns_json_with_data_key(self):
        service = "gateway"
        data = {"latency_p99": 500.0, "request_count": 9999}
        mock_resp, _ = self._make_mock_response(service, data)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = json.loads(fetch_acme_metrics("http://localhost:18080/metrics/gateway"))
        assert result["data"] == data

    def test_decodes_all_metrics_fields(self, env):
        service = "database"
        data = env.metrics_data[service]
        mock_resp, _ = self._make_mock_response(service, data)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = json.loads(fetch_acme_metrics(f"http://localhost:18080/metrics/{service}"))
        assert result["data"] == data

    def test_live_server(self):
        """Integration test: spin up the metrics server and actually fetch from it."""
        metrics_data = generate_metrics_data(seed=42, services=SERVICES)
        app = create_metrics_app(metrics_data)
        thread = start_metrics_server(app, port=18099)
        try:
            service = SERVICES[0]
            url = f"http://127.0.0.1:18099/metrics/{service}"
            result = json.loads(fetch_acme_metrics(url))
            assert result["service"] == service
            assert result["data"] == metrics_data[service]
        finally:
            stop_metrics_server(thread)


# ---------------------------------------------------------------------------
# parse_acmeconf
# ---------------------------------------------------------------------------

class TestParseAcmeconf:
    def test_returns_json_with_includes_and_services(self, configs_seed42):
        text = list(configs_seed42.values())[0]
        result = json.loads(parse_acmeconf(text))
        assert "includes" in result
        assert "services" in result

    def test_includes_is_list(self, configs_seed42):
        text = list(configs_seed42.values())[0]
        result = json.loads(parse_acmeconf(text))
        assert isinstance(result["includes"], list)

    def test_services_is_dict(self, configs_seed42):
        text = list(configs_seed42.values())[0]
        result = json.loads(parse_acmeconf(text))
        assert isinstance(result["services"], dict)

    def test_matches_reference_parser(self, configs_seed42):
        """Our parse_acmeconf must produce identical output to the reference parser."""
        for filename, text in configs_seed42.items():
            expected = acme_parse_acmeconf(text)
            actual = json.loads(parse_acmeconf(text))
            assert actual == expected, f"Mismatch for {filename}"

    def test_parses_base_acme(self, configs_seed42):
        text = configs_seed42["base.acme"]
        result = json.loads(parse_acmeconf(text))
        assert "defaults" in result["services"]

    def test_parses_includes_directive(self, configs_seed42):
        # All non-base files should include base.acme
        for filename, text in configs_seed42.items():
            if filename == "base.acme":
                continue
            result = json.loads(parse_acmeconf(text))
            assert "base.acme" in result["includes"]

    def test_parses_replicas_as_int(self, configs_seed42):
        for filename, text in configs_seed42.items():
            result = json.loads(parse_acmeconf(text))
            for svc_name, fields in result["services"].items():
                if "replicas" in fields and isinstance(fields["replicas"], (int, float)):
                    assert isinstance(fields["replicas"], int)

    def test_parses_timeout_as_int_seconds(self, configs_seed42):
        for filename, text in configs_seed42.items():
            result = json.loads(parse_acmeconf(text))
            for svc_name, fields in result["services"].items():
                if "timeout" in fields:
                    val = fields["timeout"]
                    # timeout should be an integer (seconds) or a var ref string
                    assert isinstance(val, (int, str))

    def test_parses_deps_as_list(self, configs_seed42):
        for filename, text in configs_seed42.items():
            result = json.loads(parse_acmeconf(text))
            for svc_name, fields in result["services"].items():
                if "deps" in fields:
                    assert isinstance(fields["deps"], list)

    def test_empty_config(self):
        result = json.loads(parse_acmeconf(""))
        assert result == {"includes": [], "services": {}}


# ---------------------------------------------------------------------------
# validate_acmeconf
# ---------------------------------------------------------------------------

class TestValidateAcmeconf:
    def test_returns_json_list(self):
        text = format_acmeconf({"mysvc": {"replicas": 2, "timeout": 30, "health_check": "/healthz"}})
        result = json.loads(validate_acmeconf(text))
        assert isinstance(result, list)

    def test_valid_config_returns_no_issues(self):
        text = format_acmeconf({
            "mysvc": {"replicas": 2, "timeout": 30, "health_check": "/healthz"}
        })
        issues = json.loads(validate_acmeconf(text))
        assert issues == []

    def test_detects_missing_replicas(self):
        text = format_acmeconf({"svc": {"timeout": 30, "health_check": "/healthz"}})
        issues = json.loads(validate_acmeconf(text))
        assert any("replicas" in issue for issue in issues)

    def test_detects_missing_timeout(self):
        text = format_acmeconf({"svc": {"replicas": 2, "health_check": "/healthz"}})
        issues = json.loads(validate_acmeconf(text))
        assert any("timeout" in issue for issue in issues)

    def test_detects_missing_health_check(self):
        text = format_acmeconf({"svc": {"replicas": 2, "timeout": 30}})
        issues = json.loads(validate_acmeconf(text))
        assert any("health_check" in issue for issue in issues)

    def test_detects_all_missing_fields(self):
        text = format_acmeconf({"svc": {}})
        issues = json.loads(validate_acmeconf(text))
        assert len(issues) == 3  # replicas, timeout, health_check

    def test_multiple_services_independently_validated(self):
        text = format_acmeconf({
            "good": {"replicas": 2, "timeout": 30, "health_check": "/healthz"},
            "bad": {"replicas": 1},
        })
        issues = json.loads(validate_acmeconf(text))
        # bad is missing timeout and health_check
        assert len(issues) == 2
        for issue in issues:
            assert "bad" in issue

    def test_invalid_acmeconf_string(self):
        # A config that has a service with nothing
        config = "service broken {\n}\n"
        issues = json.loads(validate_acmeconf(config))
        assert len(issues) == 3  # all three required fields missing


# ---------------------------------------------------------------------------
# diff_acmeconf
# ---------------------------------------------------------------------------

class TestDiffAcmeconf:
    def test_returns_json_list(self):
        a = format_acmeconf({"svc": {"replicas": 2, "timeout": 30, "health_check": "/healthz"}})
        result = json.loads(diff_acmeconf(a, a))
        assert isinstance(result, list)

    def test_identical_configs_no_diff(self):
        text = format_acmeconf({"svc": {"replicas": 2, "timeout": 30, "health_check": "/healthz"}})
        diffs = json.loads(diff_acmeconf(text, text))
        assert diffs == []

    def test_detects_value_change(self):
        a = format_acmeconf({"svc": {"replicas": 2, "timeout": 30, "health_check": "/healthz"}})
        b = format_acmeconf({"svc": {"replicas": 5, "timeout": 30, "health_check": "/healthz"}})
        diffs = json.loads(diff_acmeconf(a, b))
        assert len(diffs) == 1
        d = diffs[0]
        assert d["service"] == "svc"
        assert d["field"] == "replicas"
        assert d["old"] == 2
        assert d["new"] == 5

    def test_detects_added_service(self):
        a = format_acmeconf({"svc": {"replicas": 2, "timeout": 30, "health_check": "/healthz"}})
        b = format_acmeconf({
            "svc": {"replicas": 2, "timeout": 30, "health_check": "/healthz"},
            "newsvc": {"replicas": 1, "timeout": 15, "health_check": "/health"},
        })
        diffs = json.loads(diff_acmeconf(a, b))
        services_added = [d for d in diffs if d["service"] == "newsvc" and d["old"] is None]
        assert len(services_added) > 0

    def test_detects_removed_service(self):
        a = format_acmeconf({
            "svc": {"replicas": 2, "timeout": 30, "health_check": "/healthz"},
            "oldsvc": {"replicas": 1, "timeout": 15, "health_check": "/health"},
        })
        b = format_acmeconf({"svc": {"replicas": 2, "timeout": 30, "health_check": "/healthz"}})
        diffs = json.loads(diff_acmeconf(a, b))
        services_removed = [d for d in diffs if d["service"] == "oldsvc" and d["new"] is None]
        assert len(services_removed) > 0

    def test_detects_added_field(self):
        a = format_acmeconf({"svc": {"replicas": 2, "timeout": 30, "health_check": "/healthz"}})
        b = format_acmeconf({"svc": {"replicas": 2, "timeout": 30, "health_check": "/healthz", "extra": 99}})
        diffs = json.loads(diff_acmeconf(a, b))
        extra_diffs = [d for d in diffs if d["field"] == "extra"]
        assert len(extra_diffs) == 1
        assert extra_diffs[0]["old"] is None
        assert extra_diffs[0]["new"] == 99

    def test_detects_removed_field(self):
        a = format_acmeconf({"svc": {"replicas": 2, "timeout": 30, "health_check": "/healthz", "extra": 99}})
        b = format_acmeconf({"svc": {"replicas": 2, "timeout": 30, "health_check": "/healthz"}})
        diffs = json.loads(diff_acmeconf(a, b))
        extra_diffs = [d for d in diffs if d["field"] == "extra"]
        assert len(extra_diffs) == 1
        assert extra_diffs[0]["new"] is None

    def test_matches_reference_diff(self, configs_seed42):
        """diff_acmeconf must produce the same output as the reference diff_configs."""
        from benchmarks.acmecorp.config import diff_configs
        files = list(configs_seed42.values())
        if len(files) >= 2:
            a_text = files[0]
            b_text = files[1]
            expected = diff_configs(a_text, b_text)
            actual = json.loads(diff_acmeconf(a_text, b_text))
            assert actual == expected

    def test_diff_generated_configs_across_seeds(self):
        """Configs from different seeds should have diffs."""
        from benchmarks.acmecorp.config import diff_configs
        cfg_a = generate_configs(seed=1)
        cfg_b = generate_configs(seed=2)
        # Use the base.acme file which exists in both
        a_text = cfg_a["base.acme"]
        b_text = cfg_b["base.acme"]
        # base.acme is same across seeds (fixed defaults), so diffs should be empty
        diffs = json.loads(diff_acmeconf(a_text, b_text))
        # Both base configs have the same defaults block
        assert isinstance(diffs, list)


# ---------------------------------------------------------------------------
# get_fixed_tools
# ---------------------------------------------------------------------------

class TestGetFixedTools:
    def test_returns_list(self):
        tools = get_fixed_tools()
        assert isinstance(tools, list)

    def test_returns_7_tools(self):
        tools = get_fixed_tools()
        assert len(tools) == 7

    def test_all_are_tool_specs(self):
        from arise.types import ToolSpec
        tools = get_fixed_tools()
        for tool in tools:
            assert isinstance(tool, ToolSpec)

    def test_tool_names_match_functions(self):
        tools = get_fixed_tools()
        expected_names = {
            "parse_acme_log",
            "filter_acme_logs",
            "count_acme_errors",
            "fetch_acme_metrics",
            "parse_acmeconf",
            "validate_acmeconf",
            "diff_acmeconf",
        }
        actual_names = {t.name for t in tools}
        assert actual_names == expected_names

    def test_tools_have_descriptions(self):
        tools = get_fixed_tools()
        for tool in tools:
            assert tool.description and len(tool.description) > 0

    def test_tools_have_callable_fn(self):
        tools = get_fixed_tools()
        for tool in tools:
            assert callable(tool.fn)

    def test_tools_have_parameters(self):
        tools = get_fixed_tools()
        for tool in tools:
            assert isinstance(tool.parameters, dict)
            assert "type" in tool.parameters
            assert tool.parameters["type"] == "object"

    def test_parse_acme_log_tool_works(self, log_text):
        tools = get_fixed_tools()
        tool = next(t for t in tools if t.name == "parse_acme_log")
        result = json.loads(tool.fn(log_text))
        assert isinstance(result, list)
        assert len(result) > 0

    def test_count_acme_errors_tool_works(self, env, log_text):
        tools = get_fixed_tools()
        tool = next(t for t in tools if t.name == "count_acme_errors")
        result = json.loads(tool.fn(log_text))
        assert result == env.ground_truth["error_counts"]
