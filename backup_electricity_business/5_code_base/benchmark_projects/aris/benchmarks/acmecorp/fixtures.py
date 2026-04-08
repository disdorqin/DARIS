"""AcmeCorp fixture generator combining logs, metrics, and config into a seeded environment."""

from __future__ import annotations
import os
import tempfile
from dataclasses import dataclass, field

from benchmarks.acmecorp.logs import (
    generate_logs,
    ground_truth_error_counts,
    ground_truth_ctx_values,
    ground_truth_errors_by_hour,
    query_logs,
    parse_log_line,
    SERVICES,
)
from benchmarks.acmecorp.metrics import generate_metrics_data
from benchmarks.acmecorp.config import generate_configs, parse_acmeconf


@dataclass
class AcmeCorpEnv:
    logs: list[str]
    log_file_path: str
    metrics_data: dict
    metrics_port: int
    configs: dict[str, str]          # filename -> AcmeConf text
    config_data: dict[str, dict]     # filename -> parsed config
    ground_truth: dict
    _tmpdir: str = ""

    def cleanup(self):
        """Remove temp files."""
        if self._tmpdir and os.path.exists(self._tmpdir):
            import shutil
            shutil.rmtree(self._tmpdir)


def generate(seed: int = 42, log_count: int = 500, metrics_port: int = 18080) -> AcmeCorpEnv:
    """Generate a complete AcmeCorp environment. Same seed = same data."""
    # 1. Generate logs
    logs = generate_logs(seed, count=log_count)

    # 2. Write logs to a temp file
    tmpdir = tempfile.mkdtemp(prefix="acmecorp_")
    log_file_path = os.path.join(tmpdir, "acme_logs.txt")
    with open(log_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(logs))
        if logs:
            f.write("\n")

    # 3. Generate metrics data
    metrics_data = generate_metrics_data(seed, SERVICES)

    # 4. Generate configs
    configs = generate_configs(seed)

    # 5. Parse each config file
    config_data: dict[str, dict] = {}
    for filename, text in configs.items():
        config_data[filename] = parse_acmeconf(text)

    # 6. Write config files to {tmpdir}/configs/
    configs_dir = os.path.join(tmpdir, "configs")
    os.makedirs(configs_dir, exist_ok=True)
    for filename, text in configs.items():
        config_path = os.path.join(configs_dir, filename)
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(text)

    # 7. Build ground_truth dict with pre-computed answers
    error_counts = ground_truth_error_counts(logs)
    errors_by_hour = ground_truth_errors_by_hour(logs)
    total_errors = sum(error_counts.values())

    # Collect services found in config files (excluding base.acme defaults section)
    config_services = []
    config_replicas: dict[str, int] = {}
    for filename, parsed in config_data.items():
        for svc_name, svc_fields in parsed["services"].items():
            if svc_name == "defaults":
                continue
            if svc_name not in config_services:
                config_services.append(svc_name)
            replicas = svc_fields.get("replicas")
            # replicas may be a variable reference string; resolve to int if possible
            if isinstance(replicas, int):
                config_replicas[svc_name] = replicas
            elif isinstance(replicas, str):
                # Try to extract numeric default from ${VAR:-N} pattern
                import re
                m = re.search(r':-(\d+)', replicas)
                if m:
                    config_replicas[svc_name] = int(m.group(1))

    ground_truth = {
        "error_counts": error_counts,
        "errors_by_hour": errors_by_hour,
        "total_errors": total_errors,
        "services": list(SERVICES),
        "config_services": config_services,
        "config_replicas": config_replicas,
        "metrics": metrics_data,
    }

    return AcmeCorpEnv(
        logs=logs,
        log_file_path=log_file_path,
        metrics_data=metrics_data,
        metrics_port=metrics_port,
        configs=configs,
        config_data=config_data,
        ground_truth=ground_truth,
        _tmpdir=tmpdir,
    )
