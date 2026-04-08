"""Phase 3: Config Management tasks (15 tasks)."""

from __future__ import annotations

import re
from benchmarks.acmecorp.config import (
    parse_acmeconf,
    validate_config,
    diff_configs,
    resolve_variables,
    format_acmeconf,
    _VAR_RE,
)


def _find_service_config(env, service_name):
    """Find the config file and parsed data for a given service."""
    for filename, parsed in env.config_data.items():
        if service_name in parsed["services"]:
            return filename, parsed
    return None, None


def _all_config_services(env):
    """List all services defined across all config files (excluding defaults)."""
    services = []
    for filename, parsed in env.config_data.items():
        for svc in parsed["services"]:
            if svc != "defaults" and svc not in services:
                services.append(svc)
    return services


def _deps_for_service(env, service_name):
    """Get dependencies of a service from config."""
    _, parsed = _find_service_config(env, service_name)
    if parsed and service_name in parsed["services"]:
        deps = parsed["services"][service_name].get("deps", [])
        return deps if isinstance(deps, list) else []
    return []


def _health_check_for_service(env, service_name):
    """Get health_check path for a service."""
    _, parsed = _find_service_config(env, service_name)
    if parsed and service_name in parsed["services"]:
        return parsed["services"][service_name].get("health_check", "")
    return ""


def _services_depending_on(env, target):
    """Which services depend on the target service?"""
    dependents = []
    for filename, parsed in env.config_data.items():
        for svc, fields in parsed["services"].items():
            if svc == "defaults":
                continue
            deps = fields.get("deps", [])
            if isinstance(deps, list) and target in deps:
                if svc not in dependents:
                    dependents.append(svc)
    return sorted(dependents)


def _services_with_replicas_gt(env, threshold):
    """Services with replicas > threshold."""
    result = []
    for svc, replicas in env.ground_truth["config_replicas"].items():
        if replicas > threshold:
            result.append(svc)
    return sorted(result)


def _env_vars_referenced(env):
    """Find all environment variables referenced in configs."""
    var_names = set()
    for filename, text in env.configs.items():
        for m in _VAR_RE.finditer(text):
            var_names.add(m.group(1))
    return sorted(var_names)


def _check_circular_deps(env):
    """Check for circular dependencies in service configs."""
    # Build adjacency list
    adj = {}
    for filename, parsed in env.config_data.items():
        for svc, fields in parsed["services"].items():
            if svc == "defaults":
                continue
            deps = fields.get("deps", [])
            if isinstance(deps, list):
                adj[svc] = deps
            else:
                adj[svc] = []

    # DFS cycle detection
    visited = set()
    in_stack = set()
    cycles = []

    def dfs(node, path):
        if node in in_stack:
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:])
            return
        if node in visited:
            return
        visited.add(node)
        in_stack.add(node)
        path.append(node)
        for dep in adj.get(node, []):
            if dep in adj:
                dfs(dep, path[:])
        in_stack.discard(node)

    for svc in adj:
        dfs(svc, [])

    return cycles


def _validate_dep_references(env):
    """Validate that all dep references point to existing services."""
    known = _all_config_services(env)
    issues = []
    for filename, parsed in env.config_data.items():
        for svc, fields in parsed["services"].items():
            if svc == "defaults":
                continue
            deps = fields.get("deps", [])
            if isinstance(deps, list):
                for dep in deps:
                    if dep not in known:
                        issues.append(f"{svc} depends on unknown service {dep}")
    return issues


def _build_dependency_graph(env):
    """Build a dependency graph: service -> list of deps."""
    graph = {}
    for filename, parsed in env.config_data.items():
        for svc, fields in parsed["services"].items():
            if svc == "defaults":
                continue
            deps = fields.get("deps", [])
            graph[svc] = deps if isinstance(deps, list) else []
    return graph


def make_phase3_tasks(env):
    """Generate 15 Phase 3 (Config Management) tasks."""
    configs = env.configs
    config_data = env.config_data
    all_services = _all_config_services(env)

    # Pick first service for some tasks
    first_svc = all_services[0] if all_services else "payments"
    second_svc = all_services[1] if len(all_services) > 1 else "gateway"

    # Find a service that exists in config
    payments_in_config = "payments" in env.ground_truth["config_replicas"]
    gateway_in_config = "gateway" in env.ground_truth["config_replicas"]
    database_in_config = "database" in env.ground_truth["config_replicas"]

    # Get config texts for inline prompts
    main_config_text = configs.get("base.acme", "")
    first_svc_config_file = f"{first_svc}.acme"
    first_svc_config_text = configs.get(first_svc_config_file, "")
    second_svc_config_file = f"{second_svc}.acme"
    second_svc_config_text = configs.get(second_svc_config_file, "")

    # Pre-compute ground truth
    first_svc_replicas = env.ground_truth["config_replicas"].get(first_svc, 0)
    first_svc_timeout = None
    _, first_parsed = _find_service_config(env, first_svc)
    if first_parsed and first_svc in first_parsed["services"]:
        first_svc_timeout = first_parsed["services"][first_svc].get("timeout")

    second_svc_timeout = None
    _, second_parsed = _find_service_config(env, second_svc)
    if second_parsed and second_svc in second_parsed["services"]:
        second_svc_timeout = second_parsed["services"][second_svc].get("timeout")

    first_svc_deps = _deps_for_service(env, first_svc)

    # For health_check task, pick a service that has it (database if available, else first)
    hc_svc = "database" if database_in_config else first_svc
    hc_path = _health_check_for_service(env, hc_svc)

    # Validation issues
    validation_issues = []
    for filename, parsed in config_data.items():
        issues = validate_config(parsed, known_services=all_services)
        validation_issues.extend(issues)

    # Services depending on database (or first_svc)
    dep_target = "database" if database_in_config else first_svc
    dependents = _services_depending_on(env, dep_target)

    replicas_gt_2 = _services_with_replicas_gt(env, 2)
    env_vars = _env_vars_referenced(env)

    # For diff task - create a modified version
    modified_configs = {}
    for filename, text in configs.items():
        if filename != "base.acme":
            modified_configs[filename] = text
            break
    diff_file = list(modified_configs.keys())[0] if modified_configs else ""
    diff_original = modified_configs.get(diff_file, "")
    # Create modified version: change replicas
    diff_modified = diff_original.replace("replicas = 2", "replicas = 4").replace(
        "replicas = 3", "replicas = 6"
    ).replace("replicas = 5", "replicas = 8")

    circular = _check_circular_deps(env)
    invalid_deps = _validate_dep_references(env)
    dep_graph = _build_dependency_graph(env)

    tasks = []

    # --- Easy (1-5) ---

    tasks.append({
        "id": "config-01",
        "phase": 3,
        "task": (
            f"Parse the following AcmeConf config and return the replicas count "
            f"for the '{first_svc}' service.\n\n"
            f"Config file ({first_svc_config_file}):\n```\n{first_svc_config_text}```\n\n"
            f"Note: If replicas uses a variable like ${{VAR:-N}}, return the default value N."
        ),
        "check": lambda output, env, expected=first_svc_replicas: str(expected) in output,
        "difficulty": "easy",
    })

    tasks.append({
        "id": "config-02",
        "phase": 3,
        "task": (
            f"Parse the following AcmeConf config and return the timeout value "
            f"(in seconds) for the '{second_svc}' service.\n\n"
            f"Config file ({second_svc_config_file}):\n```\n{second_svc_config_text}```\n\n"
            f"Note: Durations like '30s' = 30, '5m' = 300, '1h' = 3600."
        ),
        "check": lambda output, env, expected=second_svc_timeout: (
            expected is not None and str(expected) in output
        ),
        "difficulty": "easy",
    })

    tasks.append({
        "id": "config-03",
        "phase": 3,
        "task": (
            f"Look at these AcmeConf config files and list all services defined "
            f"(excluding 'defaults').\n\n"
            + "\n\n".join(
                f"Config file ({fn}):\n```\n{text}```"
                for fn, text in configs.items()
            )
        ),
        "check": lambda output, env, expected=all_services: all(
            svc in output for svc in expected
        ),
        "difficulty": "easy",
    })

    tasks.append({
        "id": "config-04",
        "phase": 3,
        "task": (
            f"Parse the following AcmeConf config and list the dependencies "
            f"of the '{first_svc}' service.\n\n"
            f"Config file ({first_svc_config_file}):\n```\n{first_svc_config_text}```"
        ),
        "check": lambda output, env, expected=first_svc_deps: all(
            dep in output for dep in expected
        ),
        "difficulty": "easy",
    })

    tasks.append({
        "id": "config-05",
        "phase": 3,
        "task": (
            f"Parse the following AcmeConf config and return the health_check "
            f"path for the '{hc_svc}' service.\n\n"
            + (
                f"Config file ({hc_svc}.acme):\n```\n{configs.get(hc_svc + '.acme', '')}```"
                if (hc_svc + '.acme') in configs
                else f"Config file (base.acme):\n```\n{main_config_text}```"
            )
        ),
        "check": lambda output, env, expected=hc_path: (
            expected != "" and expected in output
        ),
        "difficulty": "easy",
    })

    # --- Medium (6-10) ---

    tasks.append({
        "id": "config-06",
        "phase": 3,
        "task": (
            f"Validate the following AcmeConf configs. Check if any services are "
            f"missing required fields (replicas, timeout, health_check). "
            f"Report any issues found.\n\n"
            + "\n\n".join(
                f"Config file ({fn}):\n```\n{text}```"
                for fn, text in configs.items()
            )
        ),
        "check": lambda output, env, expected=validation_issues: (
            (len(expected) == 0 and ("no " in output.lower() or "valid" in output.lower() or "none" in output.lower()))
            or all(any(word in output.lower() for word in issue.lower().split()) for issue in expected[:1])
        ),
        "difficulty": "medium",
    })

    tasks.append({
        "id": "config-07",
        "phase": 3,
        "task": (
            f"From the following AcmeConf configs, which services depend on "
            f"the '{dep_target}' service? Check the 'deps' field.\n\n"
            + "\n\n".join(
                f"Config file ({fn}):\n```\n{text}```"
                for fn, text in configs.items()
            )
        ),
        "check": lambda output, env, expected=dependents: (
            (len(expected) == 0 and ("none" in output.lower() or "no " in output.lower()))
            or all(svc in output for svc in expected)
        ),
        "difficulty": "medium",
    })

    tasks.append({
        "id": "config-08",
        "phase": 3,
        "task": (
            f"Parse all the following AcmeConf configs and list services with "
            f"replicas > 2. If replicas uses a variable like ${{VAR:-N}}, use the "
            f"default value N.\n\n"
            + "\n\n".join(
                f"Config file ({fn}):\n```\n{text}```"
                for fn, text in configs.items()
            )
        ),
        "check": lambda output, env, expected=replicas_gt_2: (
            (len(expected) == 0 and ("none" in output.lower() or "no " in output.lower()))
            or all(svc in output for svc in expected)
        ),
        "difficulty": "medium",
    })

    tasks.append({
        "id": "config-09",
        "phase": 3,
        "task": (
            f"What environment variables are referenced in the following AcmeConf "
            f"configs? Look for patterns like ${{VARIABLE_NAME}} or "
            f"${{VARIABLE_NAME:-default}}.\n\n"
            + "\n\n".join(
                f"Config file ({fn}):\n```\n{text}```"
                for fn, text in configs.items()
            )
        ),
        "check": lambda output, env, expected=env_vars: (
            (len(expected) == 0 and ("none" in output.lower() or "no " in output.lower()))
            or all(var in output for var in expected)
        ),
        "difficulty": "medium",
    })

    tasks.append({
        "id": "config-10",
        "phase": 3,
        "task": (
            f"Parse the following AcmeConf config and resolve any variable references "
            f"using their default values (e.g., ${{VAR:-3}} resolves to 3). "
            f"Return the resolved values for all fields.\n\n"
            f"Config file ({first_svc_config_file}):\n```\n{first_svc_config_text}```"
        ),
        "check": lambda output, env, expected=first_svc_replicas: str(expected) in output,
        "difficulty": "medium",
    })

    # --- Hard (11-15) ---

    tasks.append({
        "id": "config-11",
        "phase": 3,
        "task": (
            f"Compare these two versions of an AcmeConf config and list the differences.\n\n"
            f"Version A ({diff_file}):\n```\n{diff_original}```\n\n"
            f"Version B ({diff_file}):\n```\n{diff_modified}```"
        ),
        "check": lambda output, env: "replicas" in output.lower(),
        "difficulty": "hard",
    })

    tasks.append({
        "id": "config-12",
        "phase": 3,
        "task": (
            f"Check for circular dependencies in the following service configs. "
            f"A circular dependency is when service A depends on B and B depends on A "
            f"(directly or transitively).\n\n"
            + "\n\n".join(
                f"Config file ({fn}):\n```\n{text}```"
                for fn, text in configs.items()
            )
        ),
        "check": lambda output, env, expected=circular: (
            (len(expected) == 0 and ("no " in output.lower() or "none" in output.lower() or "no circular" in output.lower()))
            or len(expected) > 0
        ),
        "difficulty": "hard",
    })

    tasks.append({
        "id": "config-13",
        "phase": 3,
        "task": (
            f"Validate that all dependency references in the configs point to "
            f"existing services. Check the 'deps' field of each service and verify "
            f"each referenced service is actually defined.\n\n"
            + "\n\n".join(
                f"Config file ({fn}):\n```\n{text}```"
                for fn, text in configs.items()
            )
        ),
        "check": lambda output, env, expected=invalid_deps: (
            (len(expected) == 0 and ("valid" in output.lower() or "all " in output.lower() or "no " in output.lower()))
            or any(issue_word in output.lower() for issue in expected for issue_word in issue.lower().split())
        ),
        "difficulty": "hard",
    })

    tasks.append({
        "id": "config-14",
        "phase": 3,
        "task": (
            f"Generate a dependency graph from the following configs. For each service, "
            f"list which services it depends on.\n\n"
            + "\n\n".join(
                f"Config file ({fn}):\n```\n{text}```"
                for fn, text in configs.items()
            )
        ),
        "check": lambda output, env, expected=dep_graph: all(
            svc in output for svc in expected
        ),
        "difficulty": "hard",
    })

    tasks.append({
        "id": "config-15",
        "phase": 3,
        "task": (
            f"Perform a full config audit on the following AcmeConf files. Check for: "
            f"(1) missing required fields (replicas, timeout, health_check), "
            f"(2) unresolved variable references, "
            f"(3) invalid dependency references (deps pointing to non-existent services).\n\n"
            + "\n\n".join(
                f"Config file ({fn}):\n```\n{text}```"
                for fn, text in configs.items()
            )
        ),
        "check": lambda output, env, expected_svcs=all_services: all(
            svc in output for svc in expected_svcs
        ),
        "difficulty": "hard",
    })

    return tasks
