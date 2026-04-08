"""Phase 2: Metrics API tasks (15 tasks)."""

from __future__ import annotations

from benchmarks.acmecorp.logs import SERVICES


def make_phase2_tasks(env):
    """Generate 15 Phase 2 (Metrics API) tasks."""
    port = env.metrics_port
    metrics = env.ground_truth["metrics"]
    base_url = f"http://localhost:{port}"

    all_services = list(metrics.keys())

    # Pre-compute ground truth
    payments_p99 = metrics["payments"]["latency_p99"]
    gateway_error_rate = metrics["gateway"]["error_rate"]
    database_cpu = metrics["database"]["cpu_pct"]
    auth_request_count = metrics["auth"]["request_count"]

    highest_p99_svc = max(metrics, key=lambda s: metrics[s]["latency_p99"])
    highest_err_svc = max(metrics, key=lambda s: metrics[s]["error_rate"])

    payments_p99_val = metrics["payments"]["latency_p99"]
    gateway_p99_val = metrics["gateway"]["latency_p99"]

    high_error_svcs = [s for s in metrics if metrics[s]["error_rate"] > 0.05]
    total_requests = sum(metrics[s]["request_count"] for s in metrics)

    ranked_by_p99 = sorted(metrics, key=lambda s: metrics[s]["latency_p99"], reverse=True)

    cpu_and_error = [
        s for s in metrics
        if metrics[s]["cpu_pct"] > 80 and metrics[s]["error_rate"] > 0.05
    ]

    def health_status(error_rate):
        if error_rate < 0.05:
            return "healthy"
        elif error_rate < 0.1:
            return "degraded"
        else:
            return "critical"

    health_dashboard = {s: health_status(metrics[s]["error_rate"]) for s in metrics}

    # Most resource-efficient: lowest cpu per request
    cpu_per_req = {
        s: metrics[s]["cpu_pct"] / metrics[s]["request_count"]
        for s in metrics if metrics[s]["request_count"] > 0
    }
    most_efficient = min(cpu_per_req, key=cpu_per_req.get) if cpu_per_req else ""

    avg_error_rate = sum(metrics[s]["error_rate"] for s in metrics) / len(metrics) if metrics else 0
    services_needing_attention = [s for s in metrics if metrics[s]["error_rate"] >= 0.05]

    encoding_hint = (
        "The API returns base64-encoded data. Decode the base64 string to get the "
        "format: ACME_METRICS|service|timestamp|json. Parse the JSON portion to get metrics."
    )

    tasks = []

    # --- Easy (1-5) ---

    tasks.append({
        "id": "metrics-01",
        "phase": 2,
        "task": (
            f"Query the metrics API at {base_url}/services to list all available services. "
            f"Return the list of service names."
        ),
        "check": lambda output, env, expected=all_services: all(
            svc in output for svc in expected
        ),
        "difficulty": "easy",
    })

    tasks.append({
        "id": "metrics-02",
        "phase": 2,
        "task": (
            f"Fetch metrics for the 'payments' service from {base_url}/metrics/payments. "
            f"{encoding_hint} "
            f"Return the latency_p99 value."
        ),
        "check": lambda output, env, expected=payments_p99: str(expected) in output,
        "difficulty": "easy",
    })

    tasks.append({
        "id": "metrics-03",
        "phase": 2,
        "task": (
            f"Fetch metrics for the 'gateway' service from {base_url}/metrics/gateway. "
            f"{encoding_hint} "
            f"Return the error_rate value."
        ),
        "check": lambda output, env, expected=gateway_error_rate: str(expected) in output,
        "difficulty": "easy",
    })

    tasks.append({
        "id": "metrics-04",
        "phase": 2,
        "task": (
            f"Fetch metrics for the 'database' service from {base_url}/metrics/database. "
            f"{encoding_hint} "
            f"Return the cpu_pct value."
        ),
        "check": lambda output, env, expected=database_cpu: str(expected) in output,
        "difficulty": "easy",
    })

    tasks.append({
        "id": "metrics-05",
        "phase": 2,
        "task": (
            f"Fetch metrics for the 'auth' service from {base_url}/metrics/auth. "
            f"{encoding_hint} "
            f"Return the request_count value."
        ),
        "check": lambda output, env, expected=auth_request_count: str(expected) in output,
        "difficulty": "easy",
    })

    # --- Medium (6-10) ---

    tasks.append({
        "id": "metrics-06",
        "phase": 2,
        "task": (
            f"Check all services at {base_url}/services, then fetch metrics for each "
            f"from {base_url}/metrics/{{service}}. "
            f"{encoding_hint} "
            f"Which service has the highest latency_p99? Return the service name and value."
        ),
        "check": lambda output, env, expected=highest_p99_svc: expected in output,
        "difficulty": "medium",
    })

    tasks.append({
        "id": "metrics-07",
        "phase": 2,
        "task": (
            f"Check all services at {base_url}/services, then fetch metrics for each "
            f"from {base_url}/metrics/{{service}}. "
            f"{encoding_hint} "
            f"Which service has the highest error_rate? Return the service name and value."
        ),
        "check": lambda output, env, expected=highest_err_svc: expected in output,
        "difficulty": "medium",
    })

    tasks.append({
        "id": "metrics-08",
        "phase": 2,
        "task": (
            f"Fetch metrics for 'payments' and 'gateway' from {base_url}/metrics/{{service}}. "
            f"{encoding_hint} "
            f"Compare their latency_p99 values. Which is higher and by how much?"
        ),
        "check": lambda output, env, p=payments_p99_val, g=gateway_p99_val: (
            ("payments" in output or "gateway" in output)
        ),
        "difficulty": "medium",
    })

    tasks.append({
        "id": "metrics-09",
        "phase": 2,
        "task": (
            f"Check all services at {base_url}/services, then fetch metrics for each "
            f"from {base_url}/metrics/{{service}}. "
            f"{encoding_hint} "
            f"List all services with error_rate above 0.05."
        ),
        "check": lambda output, env, expected=high_error_svcs: (
            len(expected) == 0 or all(svc in output for svc in expected)
        ),
        "difficulty": "medium",
    })

    tasks.append({
        "id": "metrics-10",
        "phase": 2,
        "task": (
            f"Check all services at {base_url}/services, then fetch metrics for each "
            f"from {base_url}/metrics/{{service}}. "
            f"{encoding_hint} "
            f"Calculate the total request_count across all services."
        ),
        "check": lambda output, env, expected=total_requests: str(expected) in output,
        "difficulty": "medium",
    })

    # --- Hard (11-15) ---

    tasks.append({
        "id": "metrics-11",
        "phase": 2,
        "task": (
            f"Check all services at {base_url}/services, then fetch metrics for each "
            f"from {base_url}/metrics/{{service}}. "
            f"{encoding_hint} "
            f"Rank all services by latency_p99, highest first. Return the ordered list."
        ),
        "check": lambda output, env, expected=ranked_by_p99: (
            # Check that the first service appears before the last
            expected[0] in output and expected[-1] in output
            and output.index(expected[0]) < output.index(expected[-1])
        ),
        "difficulty": "hard",
    })

    tasks.append({
        "id": "metrics-12",
        "phase": 2,
        "task": (
            f"Check all services at {base_url}/services, then fetch metrics for each "
            f"from {base_url}/metrics/{{service}}. "
            f"{encoding_hint} "
            f"Find services where cpu_pct > 80 AND error_rate > 0.05. "
            f"Return the list (or state none if no services match)."
        ),
        "check": lambda output, env, expected=cpu_and_error: (
            (len(expected) == 0 and ("none" in output.lower() or "no " in output.lower()))
            or all(svc in output for svc in expected)
        ),
        "difficulty": "hard",
    })

    tasks.append({
        "id": "metrics-13",
        "phase": 2,
        "task": (
            f"Check all services at {base_url}/services, then fetch metrics for each "
            f"from {base_url}/metrics/{{service}}. "
            f"{encoding_hint} "
            f"Generate a health dashboard: for each service, report status as 'healthy' "
            f"if error_rate < 0.05, 'degraded' if error_rate < 0.1, or 'critical' otherwise."
        ),
        "check": lambda output, env, expected=health_dashboard: all(
            svc in output for svc in expected
        ),
        "difficulty": "hard",
    })

    tasks.append({
        "id": "metrics-14",
        "phase": 2,
        "task": (
            f"Check all services at {base_url}/services, then fetch metrics for each "
            f"from {base_url}/metrics/{{service}}. "
            f"{encoding_hint} "
            f"Which service is the most resource-efficient? Compute efficiency as "
            f"cpu_pct / request_count (lowest is most efficient). Return the service name."
        ),
        "check": lambda output, env, expected=most_efficient: expected in output,
        "difficulty": "hard",
    })

    tasks.append({
        "id": "metrics-15",
        "phase": 2,
        "task": (
            f"Check all services at {base_url}/services, then fetch metrics for each "
            f"from {base_url}/metrics/{{service}}. "
            f"{encoding_hint} "
            f"Generate a full metrics summary: total requests across all services, "
            f"average error rate, and list of services needing attention (error_rate >= 0.05)."
        ),
        "check": lambda output, env, expected_total=total_requests, expected_svcs=services_needing_attention: (
            str(expected_total) in output
            and all(svc in output for svc in expected_svcs)
        ),
        "difficulty": "hard",
    })

    return tasks
