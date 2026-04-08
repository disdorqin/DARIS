"""Phase 1: Log Analysis tasks (15 tasks)."""

from __future__ import annotations

import json
import re
from collections import defaultdict

from benchmarks.acmecorp.logs import parse_log_line, query_logs, SERVICES


def _count_errors_for_service(logs, service):
    """Count ERROR entries for a specific service."""
    return len(query_logs(logs, service=service, severity="ERROR"))


def _count_fatals_for_service(logs, service):
    """Count FATAL entries for a specific service."""
    return len(query_logs(logs, service=service, severity="FATAL"))


def _services_with_fatal(logs):
    """List all unique services that have FATAL entries."""
    services = set()
    for line in logs:
        parsed = parse_log_line(line)
        if parsed["severity"] == "FATAL":
            services.add(parsed["service"])
    return sorted(services)


def _severity_counts(logs):
    """Count entries per severity level."""
    counts = defaultdict(int)
    for line in logs:
        parsed = parse_log_line(line)
        counts[parsed["severity"]] += 1
    return dict(counts)


def _error_counts_per_service(logs):
    """Count ERROR+FATAL entries per service."""
    counts = defaultdict(int)
    for line in logs:
        parsed = parse_log_line(line)
        if parsed["severity"] in ("ERROR", "FATAL"):
            counts[parsed["service"]] += 1
    return dict(counts)


def _unique_user_ids_from_errors(logs):
    """Extract all unique user_ids from ERROR entries' ctx fields."""
    user_ids = set()
    for line in logs:
        parsed = parse_log_line(line)
        if parsed["severity"] == "ERROR":
            uid = parsed["ctx"].get("user_id")
            if uid:
                user_ids.add(uid)
    return sorted(user_ids)


def _errors_last_6_hours(logs):
    """Find all ERROR entries in the last 6 hours of the log timespan."""
    timestamps = [parse_log_line(line)["timestamp"] for line in logs]
    max_ts = max(timestamps)
    cutoff = max_ts - 6 * 3600
    return query_logs(logs, severity="ERROR", start_ts=cutoff)


def _hour_with_most_errors(logs):
    """Find the hour with the most errors (ERROR+FATAL)."""
    counts = defaultdict(int)
    for line in logs:
        parsed = parse_log_line(line)
        if parsed["severity"] in ("ERROR", "FATAL"):
            hour = (parsed["timestamp"] // 3600) * 3600
            counts[hour] += 1
    if not counts:
        return None
    return max(counts, key=counts.get)


def _error_rate_per_service(logs):
    """For each service, compute error rate (errors/total for that service)."""
    total = defaultdict(int)
    errors = defaultdict(int)
    for line in logs:
        parsed = parse_log_line(line)
        total[parsed["service"]] += 1
        if parsed["severity"] in ("ERROR", "FATAL"):
            errors[parsed["service"]] += 1
    return {svc: errors[svc] / total[svc] for svc in total if total[svc] > 0}


def _services_with_errors_in_same_hour(logs):
    """Correlate: which services have errors in the same hour?"""
    hour_services = defaultdict(set)
    for line in logs:
        parsed = parse_log_line(line)
        if parsed["severity"] in ("ERROR", "FATAL"):
            hour = (parsed["timestamp"] // 3600) * 3600
            hour_services[hour].add(parsed["service"])
    # Return hours where more than one service had errors
    return {h: sorted(svcs) for h, svcs in hour_services.items() if len(svcs) > 1}


def _top3_services_by_errors(logs):
    """Top 3 services by error count with their error messages."""
    counts = defaultdict(int)
    messages = defaultdict(list)
    for line in logs:
        parsed = parse_log_line(line)
        if parsed["severity"] in ("ERROR", "FATAL"):
            counts[parsed["service"]] += 1
            messages[parsed["service"]].append(parsed["message"])
    sorted_svcs = sorted(counts, key=counts.get, reverse=True)[:3]
    return {svc: {"count": counts[svc], "messages": list(set(messages[svc]))} for svc in sorted_svcs}


def _ctx_exceeds_threshold(logs):
    """Find all entries where a ctx field exceeds a threshold."""
    results = []
    for line in logs:
        parsed = parse_log_line(line)
        ctx = parsed["ctx"]
        amount = ctx.get("amount")
        if amount is not None and isinstance(amount, (int, float)) and amount > 500:
            results.append({"service": parsed["service"], "field": "amount", "value": amount})
        duration = ctx.get("duration_ms")
        if duration is not None and isinstance(duration, (int, float)) and duration > 1000:
            results.append({"service": parsed["service"], "field": "duration_ms", "value": duration})
    return results


def make_phase1_tasks(env):
    """Generate 15 Phase 1 (Log Analysis) tasks."""
    logs = env.logs

    # Pre-compute ground truth
    payments_errors = _count_errors_for_service(logs, "payments")
    gateway_errors = _count_errors_for_service(logs, "gateway")
    fatal_services = _services_with_fatal(logs)
    total_entries = len(logs)
    error_counts = _error_counts_per_service(logs)
    worst_service = max(error_counts, key=error_counts.get) if error_counts else ""
    user_ids = _unique_user_ids_from_errors(logs)
    last_6h_errors = _errors_last_6_hours(logs)
    sev_counts = _severity_counts(logs)
    peak_hour = _hour_with_most_errors(logs)
    error_rates = _error_rate_per_service(logs)
    correlated = _services_with_errors_in_same_hour(logs)
    top3 = _top3_services_by_errors(logs)
    threshold_entries = _ctx_exceeds_threshold(logs)

    # Embed log data inline so the agent can parse it from the prompt
    # Easy tasks get first 100 lines; medium/hard get all lines
    log_sample = "\n".join(logs[:100])
    log_all = "\n".join(logs)
    log_format_hint = (
        "The format is [ACME:severity:service:unix_timestamp] message | ctx={json}."
    )

    tasks = []

    # --- Easy (1-5) ---

    tasks.append({
        "id": "log-01",
        "phase": 1,
        "task": (
            f"Here is an AcmeCorp log file. {log_format_hint}\n\n"
            f"{log_sample}\n\n"
            f"How many ERROR entries are there for the 'payments' service? "
            f"Return just the count."
        ),
        "check": lambda output, env, expected=payments_errors: str(expected) in output,
        "difficulty": "easy",
    })

    tasks.append({
        "id": "log-02",
        "phase": 1,
        "task": (
            f"Here is an AcmeCorp log file. {log_format_hint}\n\n"
            f"{log_sample}\n\n"
            f"How many ERROR entries are there for the 'gateway' service? "
            f"Return just the count."
        ),
        "check": lambda output, env, expected=gateway_errors: str(expected) in output,
        "difficulty": "easy",
    })

    tasks.append({
        "id": "log-03",
        "phase": 1,
        "task": (
            f"Here is an AcmeCorp log file. {log_format_hint}\n\n"
            f"{log_sample}\n\n"
            f"List all unique services that have at least one FATAL entry. "
            f"Return the service names."
        ),
        "check": lambda output, env, expected=fatal_services: all(
            svc in output for svc in expected
        ),
        "difficulty": "easy",
    })

    tasks.append({
        "id": "log-04",
        "phase": 1,
        "task": (
            f"Here is an AcmeCorp log file. {log_format_hint}\n\n"
            f"{log_sample}\n\n"
            f"Count the total number of log entries above. "
            f"Each line is one entry. Return just the count."
        ),
        "check": lambda output, env, expected=total_entries: str(expected) in output,
        "difficulty": "easy",
    })

    tasks.append({
        "id": "log-05",
        "phase": 1,
        "task": (
            f"Here is an AcmeCorp log file. {log_format_hint}\n\n"
            f"{log_sample}\n\n"
            f"Find the service with the most error entries (ERROR + FATAL combined). "
            f"Return the service name."
        ),
        "check": lambda output, env, expected=worst_service: expected in output,
        "difficulty": "easy",
    })

    # --- Medium (6-10) ---

    tasks.append({
        "id": "log-06",
        "phase": 1,
        "task": (
            f"Here is an AcmeCorp log file. {log_format_hint}\n\n"
            f"{log_all}\n\n"
            f"Count the number of error entries (ERROR + FATAL) per service. "
            f"Return each service name with its error count."
        ),
        "check": lambda output, env, expected=error_counts: all(
            svc in output and str(cnt) in output
            for svc, cnt in expected.items()
        ),
        "difficulty": "medium",
    })

    tasks.append({
        "id": "log-07",
        "phase": 1,
        "task": (
            f"Here is an AcmeCorp log file. {log_format_hint}\n\n"
            f"{log_all}\n\n"
            f"Extract all unique user_id values from the ctx JSON field of ERROR entries. "
            f"Return the list of user_ids."
        ),
        "check": lambda output, env, expected=user_ids: (
            len(expected) == 0 or sum(1 for uid in expected if uid in output) >= len(expected) * 0.5
        ),
        "difficulty": "medium",
    })

    tasks.append({
        "id": "log-08",
        "phase": 1,
        "task": (
            f"Here is an AcmeCorp log file. {log_format_hint}\n\n"
            f"{log_all}\n\n"
            f"Find all ERROR entries in the last 6 hours of the log timespan. "
            f"Return the count of such entries."
        ),
        "check": lambda output, env, expected=len(last_6h_errors): str(expected) in output,
        "difficulty": "medium",
    })

    tasks.append({
        "id": "log-09",
        "phase": 1,
        "task": (
            f"Here is an AcmeCorp log file. {log_format_hint}\n\n"
            f"{log_all}\n\n"
            f"Count entries per severity level (DEBUG, INFO, WARN, ERROR, FATAL). "
            f"Return each severity with its count."
        ),
        "check": lambda output, env, expected=sev_counts: all(
            sev in output and str(cnt) in output
            for sev, cnt in expected.items()
        ),
        "difficulty": "medium",
    })

    tasks.append({
        "id": "log-10",
        "phase": 1,
        "task": (
            f"Here is an AcmeCorp log file. {log_format_hint}\n\n"
            f"{log_all}\n\n"
            f"Find the hour (in unix timestamp) with the most errors (ERROR + FATAL). "
            f"Return the hour's start timestamp and error count."
        ),
        "check": lambda output, env, expected=peak_hour: str(expected) in output if expected else True,
        "difficulty": "medium",
    })

    # --- Hard (11-15) ---

    tasks.append({
        "id": "log-11",
        "phase": 1,
        "task": (
            f"Here is an AcmeCorp log file. {log_format_hint}\n\n"
            f"{log_all}\n\n"
            f"For each service, compute the error rate (count of ERROR+FATAL entries "
            f"divided by total entries for that service). "
            f"Return each service with its error rate as a decimal."
        ),
        "check": lambda output, env, expected=error_rates: all(
            svc in output for svc in expected
        ),
        "difficulty": "hard",
    })

    tasks.append({
        "id": "log-12",
        "phase": 1,
        "task": (
            f"Here is an AcmeCorp log file. {log_format_hint}\n\n"
            f"{log_all}\n\n"
            f"Correlate which services have errors (ERROR or FATAL) in the same hour. "
            f"Return the hours where multiple services had errors and which services were affected."
        ),
        "check": lambda output, env, expected=correlated: (
            len(expected) == 0 or any(
                all(svc in output for svc in svcs)
                for hour, svcs in expected.items()
            )
        ),
        "difficulty": "hard",
    })

    tasks.append({
        "id": "log-13",
        "phase": 1,
        "task": (
            f"Here is an AcmeCorp log file. {log_format_hint}\n\n"
            f"{log_all}\n\n"
            f"Generate a summary of the top 3 services by error count (ERROR + FATAL). "
            f"For each, include the error count and the unique error messages."
        ),
        "check": lambda output, env, expected=top3: all(
            svc in output for svc in expected
        ),
        "difficulty": "hard",
    })

    tasks.append({
        "id": "log-14",
        "phase": 1,
        "task": (
            f"Here is an AcmeCorp log file. {log_format_hint}\n\n"
            f"{log_all}\n\n"
            f"Find all entries where a ctx field exceeds a threshold: "
            f"amount > 500 or duration_ms > 1000. "
            f"Return the count of such entries."
        ),
        "check": lambda output, env, expected=len(threshold_entries): str(expected) in output,
        "difficulty": "hard",
    })

    tasks.append({
        "id": "log-15",
        "phase": 1,
        "task": (
            f"Here is an AcmeCorp log file. {log_format_hint}\n\n"
            f"{log_all}\n\n"
            f"Generate a full error report: "
            f"(1) error counts by service (ERROR+FATAL), "
            f"(2) top error messages across all services, "
            f"(3) time distribution of errors by hour."
        ),
        "check": lambda output, env, expected=error_counts: (
            all(svc in output for svc in expected)
            and any(str(cnt) in output for cnt in expected.values())
        ),
        "difficulty": "hard",
    })

    return tasks
