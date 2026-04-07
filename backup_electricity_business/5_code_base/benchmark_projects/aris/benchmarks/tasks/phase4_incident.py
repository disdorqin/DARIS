"""Phase 4: Incident Response tasks (15 tasks)."""

from __future__ import annotations

from collections import defaultdict

from benchmarks.acmecorp.logs import parse_log_line, query_logs, SERVICES


def _error_counts_per_service(logs):
    """Count ERROR+FATAL entries per service."""
    counts = defaultdict(int)
    for line in logs:
        parsed = parse_log_line(line)
        if parsed["severity"] in ("ERROR", "FATAL"):
            counts[parsed["service"]] += 1
    return dict(counts)


def make_phase4_tasks(env):
    """Generate 15 Phase 4 (Incident Response) tasks."""
    port = env.metrics_port
    base_url = f"http://localhost:{port}"
    logs = env.logs
    metrics = env.ground_truth["metrics"]
    configs = env.configs
    config_data = env.config_data
    all_config_services = env.ground_truth["config_services"]

    encoding_hint = (
        "The metrics API returns base64-encoded data. Decode the base64 string to get "
        "format: ACME_METRICS|service|timestamp|json. Parse the JSON for metrics."
    )

    # Embed log data inline so the agent can parse it from the prompt
    log_all = "\n".join(logs)
    log_format_hint = (
        "The format is [ACME:severity:service:unix_timestamp] message | ctx={json}."
    )

    # Pre-compute
    error_counts = _error_counts_per_service(logs)
    total_errors = sum(error_counts.values())

    payments_errors = len(query_logs(logs, service="payments", severity="ERROR"))
    payments_fatals = len(query_logs(logs, service="payments", severity="FATAL"))
    payments_total_errs = payments_errors + payments_fatals

    gateway_p99 = metrics.get("gateway", {}).get("latency_p99", 0)
    gateway_warns = len(query_logs(logs, service="gateway", severity="WARN"))

    database_error_rate = metrics.get("database", {}).get("error_rate", 0)

    # Find first config service for "auth config" task
    auth_in_config = "auth" in env.ground_truth["config_replicas"]
    auth_replicas = env.ground_truth["config_replicas"].get("auth", 0)
    # If auth not in config, use first available
    config_svc_for_task = "auth" if auth_in_config else (all_config_services[0] if all_config_services else "payments")
    config_svc_replicas = env.ground_truth["config_replicas"].get(config_svc_for_task, 0)

    # Payments metrics
    payments_error_rate = metrics.get("payments", {}).get("error_rate", 0)
    payments_has_log_errors = payments_total_errs > 0
    payments_has_metric_errors = payments_error_rate > 0.05

    # Worst service by combined log errors + metric error rate
    # Rank by log error count
    worst_by_logs = max(error_counts, key=error_counts.get) if error_counts else ""
    worst_by_metrics = max(metrics, key=lambda s: metrics[s]["error_rate"]) if metrics else ""

    # Frontend config check
    frontend_in_config = "frontend" in env.ground_truth["config_replicas"]
    frontend_svc = "frontend" if frontend_in_config else (all_config_services[0] if all_config_services else "")

    # Database deps check
    database_in_config = "database" in [s for fn, p in config_data.items() for s in p["services"] if s != "defaults"]
    db_deps = []
    if database_in_config:
        for fn, parsed in config_data.items():
            if "database" in parsed["services"]:
                db_deps = parsed["services"]["database"].get("deps", [])
                if isinstance(db_deps, list):
                    break

    # Services with errors in both logs and metrics
    services_errors_both = [
        s for s in SERVICES
        if error_counts.get(s, 0) > 0 and metrics.get(s, {}).get("error_rate", 0) > 0.05
    ]

    tasks = []

    # --- Easy (1-5) ---

    tasks.append({
        "id": "incident-01",
        "phase": 4,
        "task": (
            f"INCIDENT: Payments service is alerting. Here are the logs. "
            f"{log_format_hint}\n\n{log_all}\n\n"
            f"How many ERROR entries are there for the 'payments' service?"
        ),
        "check": lambda output, env, expected=payments_errors: str(expected) in output,
        "difficulty": "easy",
    })

    tasks.append({
        "id": "incident-02",
        "phase": 4,
        "task": (
            f"INCIDENT: Gateway might be slow. Check its metrics at "
            f"{base_url}/metrics/gateway. {encoding_hint} "
            f"What is the p99 latency?"
        ),
        "check": lambda output, env, expected=gateway_p99: str(expected) in output,
        "difficulty": "easy",
    })

    tasks.append({
        "id": "incident-03",
        "phase": 4,
        "task": (
            f"INCIDENT: Someone changed the {config_svc_for_task} config. Parse "
            f"the following config and tell me the current replicas count.\n\n"
            f"Config ({config_svc_for_task}.acme):\n```\n"
            f"{configs.get(config_svc_for_task + '.acme', '')}```\n\n"
            f"Note: If replicas uses a variable like ${{VAR:-N}}, return the default value N."
        ),
        "check": lambda output, env, expected=config_svc_replicas: str(expected) in output,
        "difficulty": "easy",
    })

    tasks.append({
        "id": "incident-04",
        "phase": 4,
        "task": (
            f"INCIDENT: Check how many total errors (ERROR + FATAL) we have across "
            f"all services. Here are the logs. {log_format_hint}\n\n{log_all}\n\n"
            f"Return the total count."
        ),
        "check": lambda output, env, expected=total_errors: str(expected) in output,
        "difficulty": "easy",
    })

    tasks.append({
        "id": "incident-05",
        "phase": 4,
        "task": (
            f"INCIDENT: Fetch the error_rate for the 'database' service from metrics "
            f"at {base_url}/metrics/database. {encoding_hint} "
            f"Return the error_rate value."
        ),
        "check": lambda output, env, expected=database_error_rate: str(expected) in output,
        "difficulty": "easy",
    })

    # --- Medium (6-10) ---

    tasks.append({
        "id": "incident-06",
        "phase": 4,
        "task": (
            f"INCIDENT: Payments has errors. Check BOTH the logs below for "
            f"ERROR/FATAL entries for 'payments', and the metrics API at "
            f"{base_url}/metrics/payments. {encoding_hint}\n\n"
            f"Logs ({log_format_hint}):\n{log_all}\n\n"
            f"Are errors reflected in both the logs and the metrics? "
            f"Report the error count from logs and the error_rate from metrics."
        ),
        "check": lambda output, env, p_errs=payments_total_errs, p_rate=payments_error_rate: (
            str(p_errs) in output and ("payments" in output)
        ),
        "difficulty": "medium",
    })

    tasks.append({
        "id": "incident-07",
        "phase": 4,
        "task": (
            f"INCIDENT: Gateway is slow. Check metrics at {base_url}/metrics/gateway "
            f"for p99 latency, and check the logs below for WARN entries from "
            f"the 'gateway' service. {encoding_hint}\n\n"
            f"Logs ({log_format_hint}):\n{log_all}\n\n"
            f"Report the p99 latency and the number of WARN entries."
        ),
        "check": lambda output, env, p99=gateway_p99, warns=gateway_warns: (
            str(p99) in output and str(warns) in output
        ),
        "difficulty": "medium",
    })

    tasks.append({
        "id": "incident-08",
        "phase": 4,
        "task": (
            f"INCIDENT: We deployed a config change for '{frontend_svc}'. Check the "
            f"config below and verify the metrics look ok at "
            f"{base_url}/metrics/{frontend_svc}. {encoding_hint}\n\n"
            f"Config ({frontend_svc}.acme):\n```\n"
            f"{configs.get(frontend_svc + '.acme', 'No config available')}```\n\n"
            f"Report the config replicas and the current error_rate from metrics."
        ),
        "check": lambda output, env, svc=frontend_svc: svc in output,
        "difficulty": "medium",
    })

    tasks.append({
        "id": "incident-09",
        "phase": 4,
        "task": (
            f"INCIDENT: Multiple services have errors. Check the logs below "
            f"for error counts (ERROR+FATAL) per service and the metrics API at "
            f"{base_url} for error rates. {encoding_hint}\n\n"
            f"Logs ({log_format_hint}):\n{log_all}\n\n"
            f"Which service is the worst overall? Consider both log errors and metric error rates."
        ),
        "check": lambda output, env, w1=worst_by_logs, w2=worst_by_metrics: (
            w1 in output or w2 in output
        ),
        "difficulty": "medium",
    })

    tasks.append({
        "id": "incident-10",
        "phase": 4,
        "task": (
            f"INCIDENT: Check if the database service dependencies in the config are "
            f"all healthy in metrics. "
            + (
                f"\n\nConfig (database.acme):\n```\n{configs.get('database.acme', '')}```\n\n"
                if 'database.acme' in configs
                else f"\n\nThe database service config is:\n```\n"
                     + "\n".join(f"{fn}:\n{text}" for fn, text in configs.items())
                     + "```\n\n"
            )
            + f"For each dependency, check its metrics at {base_url}/metrics/{{service}}. "
            f"{encoding_hint} "
            f"Report whether each dependency is healthy (error_rate < 0.05)."
        ),
        "check": lambda output, env: (
            "healthy" in output.lower() or "error" in output.lower() or "rate" in output.lower()
        ),
        "difficulty": "medium",
    })

    # --- Hard (11-15) ---

    tasks.append({
        "id": "incident-11",
        "phase": 4,
        "task": (
            f"INCIDENT: Service payments is down. Perform a full investigation:\n"
            f"1. Check the logs below for ERROR/FATAL entries for payments\n"
            f"2. Check metrics at {base_url}/metrics/payments for degradation\n"
            f"3. Check the payments config below for any issues\n\n"
            + (
                f"Config (payments.acme):\n```\n{configs.get('payments.acme', '')}```\n\n"
                if 'payments.acme' in configs
                else "No payments config available.\n\n"
            )
            + f"{encoding_hint}\n\n"
            f"Logs ({log_format_hint}):\n{log_all}\n\n"
            f"What is the likely root cause?"
        ),
        "check": lambda output, env: "payments" in output.lower() and (
            "error" in output.lower() or "cause" in output.lower()
        ),
        "difficulty": "hard",
    })

    tasks.append({
        "id": "incident-12",
        "phase": 4,
        "task": (
            f"INCIDENT: We're seeing increased latency across the board. "
            f"Check all services' metrics at {base_url} (list from /services, "
            f"then /metrics/{{service}} for each). {encoding_hint}\n"
            f"Also check the logs below for correlated errors.\n\n"
            f"Logs ({log_format_hint}):\n{log_all}\n\n"
            f"Identify the bottleneck service (highest p99 latency)."
        ),
        "check": lambda output, env, expected=max(metrics, key=lambda s: metrics[s]["latency_p99"]): (
            expected in output
        ),
        "difficulty": "hard",
    })

    tasks.append({
        "id": "incident-13",
        "phase": 4,
        "task": (
            f"INCIDENT: Generate an incident report covering:\n"
            f"1. Affected services (from the logs below - services with ERROR/FATAL)\n"
            f"2. Severity assessment (from metrics at {base_url} - error rates)\n"
            f"3. Current config state\n\n"
            + "\n\n".join(
                f"Config ({fn}):\n```\n{text}```"
                for fn, text in configs.items()
            )
            + f"\n\n{encoding_hint}\n\n"
            f"Logs ({log_format_hint}):\n{log_all}"
        ),
        "check": lambda output, env, expected=error_counts: (
            sum(1 for svc in expected if svc in output) >= min(2, len(expected))
        ),
        "difficulty": "hard",
    })

    tasks.append({
        "id": "incident-14",
        "phase": 4,
        "task": (
            f"INCIDENT: Perform a full health check for each service:\n"
            f"1. Check the logs below for errors (ERROR+FATAL count)\n"
            f"2. Check metrics at {base_url}/metrics/{{service}} for performance\n"
            f"3. Check config for correctness\n\n"
            + "\n\n".join(
                f"Config ({fn}):\n```\n{text}```"
                for fn, text in configs.items()
            )
            + f"\n\n{encoding_hint}\n\n"
            f"Logs ({log_format_hint}):\n{log_all}\n\n"
            f"For each service, report: error count (logs), error rate (metrics), "
            f"and config status."
        ),
        "check": lambda output, env: (
            sum(1 for svc in SERVICES if svc in output) >= 3
        ),
        "difficulty": "hard",
    })

    tasks.append({
        "id": "incident-15",
        "phase": 4,
        "task": (
            f"INCIDENT TRIAGE: Rank all services by urgency using:\n"
            f"1. Error counts from the logs below\n"
            f"2. Error rates from metrics at {base_url}\n"
            f"3. Config validation\n\n"
            + "\n\n".join(
                f"Config ({fn}):\n```\n{text}```"
                for fn, text in configs.items()
            )
            + f"\n\n{encoding_hint}\n\n"
            f"Logs ({log_format_hint}):\n{log_all}\n\n"
            f"Return a ranked list from most urgent to least urgent, "
            f"with justification for each."
        ),
        "check": lambda output, env, w=worst_by_logs: (
            w in output and sum(1 for svc in SERVICES if svc in output) >= 3
        ),
        "difficulty": "hard",
    })

    return tasks
