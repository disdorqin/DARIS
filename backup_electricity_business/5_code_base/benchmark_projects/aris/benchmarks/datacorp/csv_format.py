"""DataCorp custom CSV dialect: pipe-delimited with ## comment headers.

Format:
    ## DataCorp Export v2 | schema=orders | exported=2024-03-01
    ## columns: order_id|customer|amount|currency|status|timestamp
    101|alice@corp.com|450.00|USD|completed|1710000000
    102|bob@corp.com|89.99|EUR|pending|1710003600

Not standard CSV:
- Header lines begin with ##
- Delimiter is pipe (|)
- Timestamps are unix integers
- First ## line contains metadata key=value pairs
- Second ## line lists column names after "columns: "
"""

from __future__ import annotations

import random
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STATUSES = ["completed", "pending", "failed", "refunded", "processing"]
CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD"]

CUSTOMERS = [
    "alice@corp.com", "bob@corp.com", "carol@corp.com", "dave@corp.com",
    "eve@corp.com", "frank@corp.com", "grace@corp.com", "henry@corp.com",
    "iris@corp.com", "jack@corp.com", "kate@corp.com", "liam@corp.com",
    "mia@corp.com", "noah@corp.com", "olivia@corp.com", "peter@corp.com",
]

PRODUCTS = [
    "widget-a", "widget-b", "gadget-pro", "gadget-lite", "service-basic",
    "service-premium", "addon-x", "addon-y", "bundle-starter", "bundle-enterprise",
]


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def generate_orders_csv(
    seed: int,
    count: int = 50,
    schema: str = "orders",
    exported_date: str = "2024-03-01",
    start_ts: int = 1710000000,
) -> str:
    """Generate a DataCorp pipe-delimited CSV with ## header comments.

    Returns the full CSV text (header + data rows).
    """
    rng = random.Random(seed)

    lines: list[str] = []
    lines.append(f"## DataCorp Export v2 | schema={schema} | exported={exported_date}")
    lines.append("## columns: order_id|customer|amount|currency|status|timestamp")

    for i in range(count):
        order_id = 100 + i + 1
        customer = rng.choice(CUSTOMERS)
        amount = round(rng.uniform(10.0, 2000.0), 2)
        currency = rng.choice(CURRENCIES)
        status = rng.choice(STATUSES)
        ts = start_ts + rng.randint(0, 86400 * 7)
        lines.append(f"{order_id}|{customer}|{amount:.2f}|{currency}|{status}|{ts}")

    return "\n".join(lines) + "\n"


def generate_products_csv(
    seed: int,
    count: int = 20,
    schema: str = "products",
    exported_date: str = "2024-03-01",
) -> str:
    """Generate a DataCorp pipe-delimited products CSV."""
    rng = random.Random(seed + 1000)

    lines: list[str] = []
    lines.append(f"## DataCorp Export v2 | schema={schema} | exported={exported_date}")
    lines.append("## columns: product_id|name|price|currency|category|in_stock")

    categories = ["hardware", "software", "service", "bundle"]
    for i in range(count):
        product_id = 200 + i + 1
        name = rng.choice(PRODUCTS)
        price = round(rng.uniform(5.0, 500.0), 2)
        currency = rng.choice(["USD", "EUR", "GBP"])
        category = rng.choice(categories)
        in_stock = rng.choice(["true", "false"])
        lines.append(f"{product_id}|{name}|{price:.2f}|{currency}|{category}|{in_stock}")

    return "\n".join(lines) + "\n"


def generate_customers_csv(
    seed: int,
    count: int = 16,
    schema: str = "customers",
    exported_date: str = "2024-03-01",
) -> str:
    """Generate a DataCorp pipe-delimited customers CSV."""
    rng = random.Random(seed + 2000)

    lines: list[str] = []
    lines.append(f"## DataCorp Export v2 | schema={schema} | exported={exported_date}")
    lines.append("## columns: customer_id|email|name|country|tier|joined_ts")

    countries = ["US", "DE", "GB", "FR", "CA", "AU", "JP"]
    tiers = ["free", "basic", "premium", "enterprise"]
    names = [
        "Alice Smith", "Bob Jones", "Carol White", "Dave Brown",
        "Eve Davis", "Frank Miller", "Grace Wilson", "Henry Moore",
        "Iris Taylor", "Jack Anderson", "Kate Thomas", "Liam Jackson",
        "Mia Harris", "Noah Martin", "Olivia Garcia", "Peter Martinez",
    ]

    used_emails = list(CUSTOMERS)
    rng.shuffle(used_emails)

    for i in range(min(count, len(CUSTOMERS))):
        customer_id = 300 + i + 1
        email = CUSTOMERS[i]
        name = names[i % len(names)]
        country = rng.choice(countries)
        tier = rng.choice(tiers)
        joined_ts = 1680000000 + rng.randint(0, 86400 * 365)
        lines.append(f"{customer_id}|{email}|{name}|{country}|{tier}|{joined_ts}")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_datacorp_csv(text: str) -> dict[str, Any]:
    """Parse a DataCorp pipe-delimited CSV into structured data.

    Returns:
        {
            "metadata": {"schema": str, "exported": str, ...},
            "columns": list[str],
            "rows": list[dict],   # column -> value
            "raw_rows": list[list[str]],
        }
    """
    lines = text.splitlines()
    metadata: dict[str, str] = {}
    columns: list[str] = []
    raw_rows: list[list[str]] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("## columns:"):
            # "## columns: order_id|customer|amount|currency|status|timestamp"
            cols_part = stripped[len("## columns:"):].strip()
            columns = [c.strip() for c in cols_part.split("|")]

        elif stripped.startswith("##"):
            # "## DataCorp Export v2 | schema=orders | exported=2024-03-01"
            meta_part = stripped[2:].strip()
            # Split on " | " but skip the first segment if it doesn't have "="
            segments = [s.strip() for s in meta_part.split("|")]
            for seg in segments:
                seg = seg.strip()
                if "=" in seg:
                    key, _, val = seg.partition("=")
                    metadata[key.strip()] = val.strip()
                else:
                    # Version string like "DataCorp Export v2"
                    metadata["_version"] = seg

        else:
            # Data row
            raw_rows.append([f.strip() for f in stripped.split("|")])

    # Build typed row dicts
    rows: list[dict] = []
    for raw in raw_rows:
        if len(raw) != len(columns):
            continue  # skip malformed rows
        row: dict[str, Any] = {}
        for col, val in zip(columns, raw):
            # Auto-cast numeric fields
            row[col] = _auto_cast(col, val)
        rows.append(row)

    return {
        "metadata": metadata,
        "columns": columns,
        "rows": rows,
        "raw_rows": raw_rows,
    }


def _auto_cast(col: str, val: str) -> Any:
    """Try to cast value to int or float based on column name and value."""
    # Known integer columns
    if col in ("timestamp", "order_id", "product_id", "customer_id", "joined_ts"):
        try:
            return int(val)
        except ValueError:
            return val
    # Known float columns
    if col in ("amount", "price"):
        try:
            return float(val)
        except ValueError:
            return val
    # Try numeric fallback
    try:
        int_val = int(val)
        return int_val
    except ValueError:
        pass
    try:
        float_val = float(val)
        return float_val
    except ValueError:
        pass
    return val


# ---------------------------------------------------------------------------
# Ground-truth helpers
# ---------------------------------------------------------------------------

def gt_row_count(parsed: dict) -> int:
    """Return number of data rows."""
    return len(parsed["rows"])


def gt_column_values(parsed: dict, column: str) -> list:
    """Return list of values for a column."""
    return [row[column] for row in parsed["rows"] if column in row]


def gt_filter_rows(parsed: dict, column: str, value: Any) -> list[dict]:
    """Return rows where column equals value."""
    return [row for row in parsed["rows"] if row.get(column) == value]


def gt_sum_by_group(parsed: dict, value_col: str, group_col: str) -> dict[str, float]:
    """Sum value_col grouped by group_col."""
    result: dict[str, float] = {}
    for row in parsed["rows"]:
        key = str(row.get(group_col, ""))
        val = row.get(value_col, 0)
        if isinstance(val, (int, float)):
            result[key] = round(result.get(key, 0.0) + val, 4)
    return result


def gt_detect_duplicates(parsed: dict, key_col: str) -> list[Any]:
    """Return values of key_col that appear more than once."""
    from collections import Counter
    counts = Counter(row.get(key_col) for row in parsed["rows"])
    return [k for k, v in counts.items() if v > 1]


def gt_join_csvs(
    left_parsed: dict,
    right_parsed: dict,
    left_key: str,
    right_key: str,
) -> list[dict]:
    """Inner join two parsed CSVs on the given key columns."""
    index: dict[Any, list[dict]] = {}
    for row in right_parsed["rows"]:
        k = row.get(right_key)
        if k not in index:
            index[k] = []
        index[k].append(row)

    result = []
    for left_row in left_parsed["rows"]:
        k = left_row.get(left_key)
        for right_row in index.get(k, []):
            merged = {**left_row, **{f"r_{col}": val for col, val in right_row.items()}}
            result.append(merged)
    return result


def gt_pivot_status_by_currency(parsed: dict) -> dict[str, dict[str, int]]:
    """Pivot table: currency × status → count of orders."""
    result: dict[str, dict[str, int]] = {}
    for row in parsed["rows"]:
        currency = str(row.get("currency", ""))
        status = str(row.get("status", ""))
        if currency not in result:
            result[currency] = {}
        result[currency][status] = result[currency].get(status, 0) + 1
    return result


def gt_running_average(parsed: dict, value_col: str) -> list[float]:
    """Return running average of value_col across rows in order."""
    running: list[float] = []
    total = 0.0
    for i, row in enumerate(parsed["rows"], 1):
        val = row.get(value_col, 0)
        if isinstance(val, (int, float)):
            total += val
            running.append(round(total / i, 4))
    return running
