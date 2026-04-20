"""Hand-written baseline tools for AcmeCorp formats.

These represent "an engineer spent an afternoon building tools."
Each tool is a self-contained function with all imports inside the body.
Each takes string input and returns string output.
"""


def parse_acme_log(log_text: str) -> str:
    """Parse AcmeCorp log lines. Returns JSON array of parsed entries."""
    import json
    import re

    LOG_RE = re.compile(
        r"^\[ACME:(?P<severity>[A-Z]+):(?P<service>[a-z]+):(?P<timestamp>\d+)\] "
        r"(?P<message>.+?) \| ctx=(?P<ctx>\{.*\})$"
    )

    entries = []
    for line in log_text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = LOG_RE.match(line)
        if not m:
            continue
        entry = {
            "severity": m.group("severity"),
            "service": m.group("service"),
            "timestamp": int(m.group("timestamp")),
            "message": m.group("message"),
            "ctx": json.loads(m.group("ctx")),
        }
        entries.append(entry)

    return json.dumps(entries)


def filter_acme_logs(log_text: str, service: str = "", severity: str = "") -> str:
    """Filter AcmeCorp log entries by service and/or severity. Returns matching lines."""
    import re

    LOG_RE = re.compile(
        r"^\[ACME:(?P<severity>[A-Z]+):(?P<service>[a-z]+):(?P<timestamp>\d+)\] "
        r"(?P<message>.+?) \| ctx=(?P<ctx>\{.*\})$"
    )

    results = []
    for line in log_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        m = LOG_RE.match(stripped)
        if not m:
            continue
        if service and m.group("service") != service:
            continue
        if severity and m.group("severity") != severity.upper():
            continue
        results.append(stripped)

    return "\n".join(results)


def count_acme_errors(log_text: str) -> str:
    """Count ERROR and FATAL entries per service. Returns JSON: {"service": count}."""
    import json
    import re
    from collections import defaultdict

    LOG_RE = re.compile(
        r"^\[ACME:(?P<severity>[A-Z]+):(?P<service>[a-z]+):(?P<timestamp>\d+)\] "
        r"(?P<message>.+?) \| ctx=(?P<ctx>\{.*\})$"
    )

    counts: dict = defaultdict(int)
    for line in log_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        m = LOG_RE.match(stripped)
        if not m:
            continue
        if m.group("severity") in ("ERROR", "FATAL"):
            counts[m.group("service")] += 1

    return json.dumps(dict(counts))


def fetch_acme_metrics(url: str) -> str:
    """Fetch and decode AcmeCorp metrics from the API. URL should be like http://host:port/metrics/service. Returns decoded JSON metrics."""
    import urllib.request
    import base64
    import json

    with urllib.request.urlopen(url) as resp:
        body = resp.read().decode("utf-8").strip()

    # Decode base64 payload: ACME_METRICS|service|timestamp|{json}
    raw = base64.b64decode(body.encode("utf-8")).decode("utf-8")
    parts = raw.split("|", 3)
    if len(parts) != 4 or parts[0] != "ACME_METRICS":
        raise ValueError(f"Invalid ACME payload: {raw!r}")
    _, service, ts_str, json_data = parts
    result = {
        "service": service,
        "timestamp": int(ts_str),
        "data": json.loads(json_data),
    }
    return json.dumps(result)


def parse_acmeconf(config_text: str) -> str:
    """Parse AcmeConf format. Returns JSON with services and their settings."""
    import json
    import re

    DURATION_RE = re.compile(r'^(\d+)(s|m|h)$')
    DURATION_UNITS = {'s': 1, 'm': 60, 'h': 3600}
    VAR_RE = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-(.*?))?\}')

    def parse_value(raw: str):
        raw = raw.strip()
        # List value
        if raw.startswith('[') and raw.endswith(']'):
            inner = raw[1:-1]
            items = [item.strip().strip('"') for item in inner.split(',') if item.strip()]
            return items
        # Quoted string
        if raw.startswith('"') and raw.endswith('"'):
            return raw[1:-1]
        # Variable reference — preserve as-is
        if VAR_RE.search(raw):
            return raw
        # Duration literal
        dm = DURATION_RE.match(raw)
        if dm:
            return int(dm.group(1)) * DURATION_UNITS[dm.group(2)]
        # Integer
        try:
            return int(raw)
        except ValueError:
            pass
        # Unquoted string
        return raw

    result = {'includes': [], 'services': {}}
    current_service = None
    brace_depth = 0

    for line in config_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # @include directive
        m = re.match(r'@include\s+"([^"]+)"', stripped)
        if m:
            result['includes'].append(m.group(1))
            continue

        # Service block open
        m = re.match(r'^service\s+(\w+)\s*\{', stripped)
        if m:
            current_service = m.group(1)
            result['services'][current_service] = {}
            brace_depth += 1
            continue

        # Block close
        if stripped == '}':
            brace_depth -= 1
            if brace_depth == 0:
                current_service = None
            continue

        # Key = value inside a service block
        if current_service is not None and '=' in stripped:
            key, _, value_raw = stripped.partition('=')
            key = key.strip()
            value_raw = value_raw.strip()
            result['services'][current_service][key] = parse_value(value_raw)

    return json.dumps(result)


def validate_acmeconf(config_text: str) -> str:
    """Validate AcmeConf config. Returns JSON list of issues found."""
    import json
    import re

    DURATION_RE = re.compile(r'^(\d+)(s|m|h)$')
    DURATION_UNITS = {'s': 1, 'm': 60, 'h': 3600}
    VAR_RE = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-(.*?))?\}')

    def parse_value(raw: str):
        raw = raw.strip()
        if raw.startswith('[') and raw.endswith(']'):
            inner = raw[1:-1]
            return [item.strip().strip('"') for item in inner.split(',') if item.strip()]
        if raw.startswith('"') and raw.endswith('"'):
            return raw[1:-1]
        if VAR_RE.search(raw):
            return raw
        dm = DURATION_RE.match(raw)
        if dm:
            return int(dm.group(1)) * DURATION_UNITS[dm.group(2)]
        try:
            return int(raw)
        except ValueError:
            pass
        return raw

    parsed = {'includes': [], 'services': {}}
    current_service = None
    brace_depth = 0

    for line in config_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        m = re.match(r'@include\s+"([^"]+)"', stripped)
        if m:
            parsed['includes'].append(m.group(1))
            continue
        m = re.match(r'^service\s+(\w+)\s*\{', stripped)
        if m:
            current_service = m.group(1)
            parsed['services'][current_service] = {}
            brace_depth += 1
            continue
        if stripped == '}':
            brace_depth -= 1
            if brace_depth == 0:
                current_service = None
            continue
        if current_service is not None and '=' in stripped:
            key, _, value_raw = stripped.partition('=')
            parsed['services'][current_service][key.strip()] = parse_value(value_raw.strip())

    required_fields = {'replicas', 'timeout', 'health_check'}
    issues = []

    for svc_name, fields in parsed['services'].items():
        for req in sorted(required_fields):
            if req not in fields:
                issues.append(f"Service '{svc_name}' is missing required field '{req}'")

    return json.dumps(issues)


def diff_acmeconf(config_a: str, config_b: str) -> str:
    """Diff two AcmeConf configs. Returns JSON list of changes."""
    import json
    import re

    DURATION_RE = re.compile(r'^(\d+)(s|m|h)$')
    DURATION_UNITS = {'s': 1, 'm': 60, 'h': 3600}
    VAR_RE = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-(.*?))?\}')

    def parse_value(raw: str):
        raw = raw.strip()
        if raw.startswith('[') and raw.endswith(']'):
            inner = raw[1:-1]
            return [item.strip().strip('"') for item in inner.split(',') if item.strip()]
        if raw.startswith('"') and raw.endswith('"'):
            return raw[1:-1]
        if VAR_RE.search(raw):
            return raw
        dm = DURATION_RE.match(raw)
        if dm:
            return int(dm.group(1)) * DURATION_UNITS[dm.group(2)]
        try:
            return int(raw)
        except ValueError:
            pass
        return raw

    def parse(text: str) -> dict:
        result = {'services': {}}
        current_service = None
        brace_depth = 0
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            if stripped.startswith('@include'):
                continue
            m = re.match(r'^service\s+(\w+)\s*\{', stripped)
            if m:
                current_service = m.group(1)
                result['services'][current_service] = {}
                brace_depth += 1
                continue
            if stripped == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    current_service = None
                continue
            if current_service is not None and '=' in stripped:
                key, _, value_raw = stripped.partition('=')
                result['services'][current_service][key.strip()] = parse_value(value_raw.strip())
        return result

    a = parse(config_a)['services']
    b = parse(config_b)['services']

    diffs = []
    all_services = sorted(set(a) | set(b))

    for svc in all_services:
        if svc not in a:
            for field, new_val in b[svc].items():
                diffs.append({'service': svc, 'field': field, 'old': None, 'new': new_val})
        elif svc not in b:
            for field, old_val in a[svc].items():
                diffs.append({'service': svc, 'field': field, 'old': old_val, 'new': None})
        else:
            all_fields = sorted(set(a[svc]) | set(b[svc]))
            for field in all_fields:
                old_val = a[svc].get(field)
                new_val = b[svc].get(field)
                if field not in a[svc]:
                    diffs.append({'service': svc, 'field': field, 'old': None, 'new': new_val})
                elif field not in b[svc]:
                    diffs.append({'service': svc, 'field': field, 'old': old_val, 'new': None})
                elif old_val != new_val:
                    diffs.append({'service': svc, 'field': field, 'old': old_val, 'new': new_val})

    return json.dumps(diffs)


def get_fixed_tools() -> list:
    """Return all baseline tools as ARISE ToolSpec objects."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
    from arise.types import ToolSpec, _extract_parameters

    tools = [
        parse_acme_log,
        filter_acme_logs,
        count_acme_errors,
        fetch_acme_metrics,
        parse_acmeconf,
        validate_acmeconf,
        diff_acmeconf,
    ]
    specs = []
    for fn in tools:
        parameters = _extract_parameters(fn)
        spec = ToolSpec(
            name=fn.__name__,
            description=fn.__doc__ or "",
            parameters=parameters,
            fn=fn,
        )
        specs.append(spec)
    return specs
