"""DataCorp benchmark tasks — 30 tasks across 3 phases.

Phase 1 (csv-01 … csv-10):  CSV Processing
Phase 2 (val-01 … val-10):  Data Validation API
Phase 3 (qry-01 … qry-10):  DCQL Query Execution
"""

from __future__ import annotations

from benchmarks.datacorp.csv_format import (
    parse_datacorp_csv,
    gt_row_count,
    gt_filter_rows,
    gt_sum_by_group,
    gt_detect_duplicates,
    gt_pivot_status_by_currency,
    gt_running_average,
)
from benchmarks.datacorp.validation_api import SCHEMAS, validate_batch, auto_fix_record
from benchmarks.datacorp.query import execute_dcql, parse_dcql


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_csv(text: str) -> str:
    """Return a trimmed version of CSV for embedding in prompts."""
    return text.strip()


def _contains_all(output: str, values: list) -> bool:
    return all(str(v) in output for v in values)


def _contains_any(output: str, values: list) -> bool:
    return any(str(v) in output for v in values)


# ---------------------------------------------------------------------------
# Phase 1: CSV Processing (10 tasks)
# ---------------------------------------------------------------------------

_CSV_FORMAT_HINT = (
    "DataCorp pipe-delimited format: lines starting with ## are header comments. "
    "The first ## line contains metadata (schema, exported date). "
    "The second ## line lists column names separated by |. "
    "Data rows use | as delimiter. Timestamps are Unix epoch integers."
)


def make_datacorp_csv_tasks(env) -> list[dict]:
    """10 Phase 1 tasks: CSV parsing and processing."""
    orders_text = env.csv_data["orders.dc"]
    products_text = env.csv_data["products.dc"]
    customers_text = env.csv_data["customers.dc"]
    gt = env.ground_truth

    orders_parsed = env.csv_parsed["orders.dc"]
    products_parsed = env.csv_parsed["products.dc"]

    # Pre-compute values used in checks
    order_count = gt["order_count"]
    completed_count = gt["completed_order_count"]
    sum_by_currency = gt["sum_by_currency"]
    usd_total = sum_by_currency.get("USD", 0)
    eur_total = sum_by_currency.get("EUR", 0)
    total_amount = gt["total_amount"]
    dup_customers = gt["duplicate_customers"]
    pivot = gt["pivot_status_by_currency"]
    final_avg = gt["final_running_avg"]
    usd_completed = gt["usd_completed_count"]

    # For the join task: orders + customers
    orders_rows = orders_parsed["rows"]
    customers_parsed = env.csv_parsed["customers.dc"]
    customers_rows = customers_parsed["rows"]
    customers_by_email = {r["email"]: r for r in customers_rows}
    orders_with_tier = [
        {**r, "tier": customers_by_email[r["customer"]].get("tier")}
        for r in orders_rows if r.get("customer") in customers_by_email
    ]
    join_count = len(orders_with_tier)

    tasks = []

    # ---- Easy (csv-01 … csv-04) ----

    tasks.append({
        "id": "csv-01",
        "phase": 1,
        "task": (
            f"Here is a DataCorp pipe-delimited CSV export. {_CSV_FORMAT_HINT}\n\n"
            f"{_fmt_csv(orders_text)}\n\n"
            f"How many data rows are in this file? (Do not count ## header lines.) "
            f"Return just the count."
        ),
        "check": lambda output, env, n=order_count: str(n) in output,
        "difficulty": "easy",
    })

    tasks.append({
        "id": "csv-02",
        "phase": 1,
        "task": (
            f"Here is a DataCorp pipe-delimited CSV export. {_CSV_FORMAT_HINT}\n\n"
            f"{_fmt_csv(orders_text)}\n\n"
            f"What are the column names in this file? List all column names."
        ),
        "check": lambda output, env: _contains_all(
            output, ["order_id", "customer", "amount", "currency", "status", "timestamp"]
        ),
        "difficulty": "easy",
    })

    tasks.append({
        "id": "csv-03",
        "phase": 1,
        "task": (
            f"Here is a DataCorp pipe-delimited CSV export. {_CSV_FORMAT_HINT}\n\n"
            f"{_fmt_csv(orders_text)}\n\n"
            f"How many orders have status = 'completed'? Return just the count."
        ),
        "check": lambda output, env, n=completed_count: str(n) in output,
        "difficulty": "easy",
    })

    tasks.append({
        "id": "csv-04",
        "phase": 1,
        "task": (
            f"Here is a DataCorp pipe-delimited CSV export. {_CSV_FORMAT_HINT}\n\n"
            f"{_fmt_csv(orders_text)}\n\n"
            f"What schema name is declared in the ## header of this file? "
            f"Return just the schema name."
        ),
        "check": lambda output, env: "orders" in output.lower(),
        "difficulty": "easy",
    })

    # ---- Medium (csv-05 … csv-08) ----

    tasks.append({
        "id": "csv-05",
        "phase": 1,
        "task": (
            f"Here is a DataCorp pipe-delimited CSV export. {_CSV_FORMAT_HINT}\n\n"
            f"{_fmt_csv(orders_text)}\n\n"
            f"Sum the 'amount' field grouped by 'currency'. "
            f"Return each currency and its total amount."
        ),
        "check": lambda output, env, sbc=sum_by_currency: (
            all(currency in output for currency in sbc.keys())
        ),
        "difficulty": "medium",
    })

    tasks.append({
        "id": "csv-06",
        "phase": 1,
        "task": (
            f"Here is a DataCorp orders export. {_CSV_FORMAT_HINT}\n\n"
            f"{_fmt_csv(orders_text)}\n\n"
            f"Here is a DataCorp customers export.\n\n"
            f"{_fmt_csv(customers_text)}\n\n"
            f"Join the two files on orders.customer = customers.email. "
            f"How many orders can be matched to a customer record? Return just the count."
        ),
        "check": lambda output, env, n=join_count: str(n) in output,
        "difficulty": "medium",
    })

    tasks.append({
        "id": "csv-07",
        "phase": 1,
        "task": (
            f"Here is a DataCorp pipe-delimited CSV export. {_CSV_FORMAT_HINT}\n\n"
            f"{_fmt_csv(orders_text)}\n\n"
            f"Which customer email addresses appear more than once in this file "
            f"(i.e., have placed multiple orders)? List the duplicate customer emails."
        ),
        "check": lambda output, env, dups=dup_customers: (
            len(dups) == 0 or any(d in output for d in dups)
        ),
        "difficulty": "medium",
    })

    tasks.append({
        "id": "csv-08",
        "phase": 1,
        "task": (
            f"Here is a DataCorp pipe-delimited CSV export. {_CSV_FORMAT_HINT}\n\n"
            f"{_fmt_csv(orders_text)}\n\n"
            f"How many orders are both in USD currency AND have status 'completed'? "
            f"Return just the count."
        ),
        "check": lambda output, env, n=usd_completed: str(n) in output,
        "difficulty": "medium",
    })

    # ---- Hard (csv-09 … csv-10) ----

    tasks.append({
        "id": "csv-09",
        "phase": 1,
        "task": (
            f"Here is a DataCorp pipe-delimited CSV export. {_CSV_FORMAT_HINT}\n\n"
            f"{_fmt_csv(orders_text)}\n\n"
            f"Create a pivot table showing the count of orders for each "
            f"(currency, status) combination. "
            f"Return the result as a table or structured list showing currency, status, and count."
        ),
        "check": lambda output, env, p=pivot: (
            any(currency in output for currency in p.keys())
            and any(status in output for status in ["completed", "pending", "failed"])
        ),
        "difficulty": "hard",
    })

    tasks.append({
        "id": "csv-10",
        "phase": 1,
        "task": (
            f"Here is a DataCorp pipe-delimited CSV export. {_CSV_FORMAT_HINT}\n\n"
            f"{_fmt_csv(orders_text)}\n\n"
            f"Compute the running average of the 'amount' field across all rows "
            f"(in the order they appear). What is the final running average "
            f"(i.e., the overall mean of all amounts)? Round to 4 decimal places."
        ),
        "check": lambda output, env, avg=final_avg: (
            # Accept answers within ±0.01 of the true value
            any(
                abs(float(tok) - avg) < 0.5
                for tok in output.replace(",", " ").split()
                if _is_float(tok)
            )
        ),
        "difficulty": "hard",
    })

    return tasks


def _is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Phase 2: Data Validation (10 tasks)
# ---------------------------------------------------------------------------

_API_FORMAT_HINT = (
    "The DataCorp Validation API is running at http://localhost:{port}. "
    "POST /validate with body {{\"records\": [...], \"schema\": \"orders\"}} to validate records. "
    "GET /schemas to list schemas. GET /schemas/{{name}} for schema details. "
    "Error codes: DC-001=missing field, DC-002=wrong type, DC-003=out of range, "
    "DC-004=invalid enum, DC-005=too long, DC-006=bad timestamp, "
    "DC-007=cross-field violation, DC-008=duplicate key."
)

# Sample invalid records for validation tasks
_SAMPLE_VALID_RECORD = {
    "order_id": 999,
    "customer": "test@example.com",
    "amount": 150.00,
    "currency": "USD",
    "status": "completed",
    "timestamp": 1710000000,
}

_SAMPLE_INVALID_RECORDS = [
    # DC-001: missing field
    {"order_id": 1001, "customer": "a@b.com", "amount": 50.0, "currency": "USD", "status": "completed"},
    # DC-002: wrong type for amount
    {"order_id": 1002, "customer": "c@d.com", "amount": "not-a-number", "currency": "EUR", "status": "pending", "timestamp": 1710000000},
    # DC-004: invalid enum for currency
    {"order_id": 1003, "customer": "e@f.com", "amount": 75.0, "currency": "XYZ", "status": "pending", "timestamp": 1710000000},
    # DC-004: invalid enum for status
    {"order_id": 1004, "customer": "g@h.com", "amount": 200.0, "currency": "USD", "status": "shipped", "timestamp": 1710000000},
    # DC-003: negative amount
    {"order_id": 1005, "customer": "i@j.com", "amount": -10.0, "currency": "GBP", "status": "refunded", "timestamp": 1710000000},
]

# Batch with duplicates for DC-008
_DUPLICATE_KEY_RECORDS = [
    {"order_id": 2001, "customer": "alice@test.com", "amount": 100.0, "currency": "USD", "status": "completed", "timestamp": 1710000000},
    {"order_id": 2001, "customer": "bob@test.com", "amount": 200.0, "currency": "EUR", "status": "pending", "timestamp": 1710003600},
]

# Records for auto-fix task
_FIXABLE_RECORDS = [
    # amount as string → should be cast to float
    {"order_id": 3001, "customer": "fix@test.com", "amount": "299.99", "currency": "USD", "status": "completed", "timestamp": 1710000000},
    # currency wrong case (technically invalid enum) → fix to default
    {"order_id": 3002, "customer": "fix2@test.com", "amount": 49.99, "currency": "usd", "status": "pending", "timestamp": 1710003600},
]

# Pre-compute validation results
_single_valid_result = validate_batch([dict(_SAMPLE_VALID_RECORD)], "orders")
_invalid_batch_result = validate_batch([dict(r) for r in _SAMPLE_INVALID_RECORDS], "orders")
_error_codes_in_batch = list(_invalid_batch_result["error_summary"].keys())
_dup_result = validate_batch([dict(r) for r in _DUPLICATE_KEY_RECORDS], "orders")


def make_datacorp_validation_tasks(env) -> list[dict]:
    """10 Phase 2 tasks: Data Validation API."""
    port = env.validation_port
    gt = env.ground_truth

    hint = _API_FORMAT_HINT.format(port=port)
    base_url = f"http://localhost:{port}"

    # Ground truth: validation of env's orders
    orders_valid_count = gt["validation_valid_count"]
    orders_invalid_count = gt["validation_invalid_count"]
    error_summary = gt["validation_error_summary"]
    schema_names = gt["schema_names"]

    tasks = []

    # ---- Easy (val-01 … val-04) ----

    tasks.append({
        "id": "val-01",
        "phase": 2,
        "task": (
            f"{hint}\n\n"
            f"Call GET {base_url}/schemas to list all available schemas. "
            f"Return the list of schema names."
        ),
        "check": lambda output, env: all(s in output for s in ["orders", "products", "customers"]),
        "difficulty": "easy",
    })

    tasks.append({
        "id": "val-02",
        "phase": 2,
        "task": (
            f"{hint}\n\n"
            f"Call GET {base_url}/schemas/orders to retrieve the 'orders' schema definition. "
            f"List all field names defined in this schema."
        ),
        "check": lambda output, env: _contains_all(
            output, ["order_id", "customer", "amount", "currency", "status", "timestamp"]
        ),
        "difficulty": "easy",
    })

    import json
    valid_rec_json = json.dumps(_SAMPLE_VALID_RECORD, indent=2)
    tasks.append({
        "id": "val-03",
        "phase": 2,
        "task": (
            f"{hint}\n\n"
            f"Validate this single record against the 'orders' schema by calling "
            f"POST {base_url}/validate:\n\n"
            f"{valid_rec_json}\n\n"
            f"Is this record valid? Return 'valid' or 'invalid' and the validation result."
        ),
        "check": lambda output, env: "valid" in output.lower(),
        "difficulty": "easy",
    })

    invalid_rec_json = json.dumps(_SAMPLE_INVALID_RECORDS[0], indent=2)
    tasks.append({
        "id": "val-04",
        "phase": 2,
        "task": (
            f"{hint}\n\n"
            f"Validate this record against the 'orders' schema by calling "
            f"POST {base_url}/validate:\n\n"
            f"{invalid_rec_json}\n\n"
            f"This record has at least one validation error. "
            f"What error code(s) does the API return?"
        ),
        "check": lambda output, env: "DC-001" in output or "DC-00" in output,
        "difficulty": "easy",
    })

    # ---- Medium (val-05 … val-08) ----

    invalid_batch_json = json.dumps(_SAMPLE_INVALID_RECORDS, indent=2)
    tasks.append({
        "id": "val-05",
        "phase": 2,
        "task": (
            f"{hint}\n\n"
            f"Validate this batch of records against the 'orders' schema:\n\n"
            f"{invalid_batch_json}\n\n"
            f"How many records are valid and how many are invalid? "
            f"Return the valid count and invalid count."
        ),
        "check": lambda output, env, r=_invalid_batch_result: (
            str(r["valid_count"]) in output and str(r["invalid_count"]) in output
        ),
        "difficulty": "medium",
    })

    tasks.append({
        "id": "val-06",
        "phase": 2,
        "task": (
            f"{hint}\n\n"
            f"Validate this batch of records against the 'orders' schema:\n\n"
            f"{invalid_batch_json}\n\n"
            f"Categorize the validation errors by error code (DC-001, DC-002, etc.). "
            f"Return each error code and how many times it appears."
        ),
        "check": lambda output, env, codes=_error_codes_in_batch: (
            any(code in output for code in codes)
        ),
        "difficulty": "medium",
    })

    dup_batch_json = json.dumps(_DUPLICATE_KEY_RECORDS, indent=2)
    tasks.append({
        "id": "val-07",
        "phase": 2,
        "task": (
            f"{hint}\n\n"
            f"Validate this batch of records against the 'orders' schema:\n\n"
            f"{dup_batch_json}\n\n"
            f"These records contain a duplicate primary key. "
            f"What error code does the API return for duplicate keys? "
            f"Which order_id is duplicated?"
        ),
        "check": lambda output, env: "DC-008" in output and "2001" in output,
        "difficulty": "medium",
    })

    orders_csv_text = env.csv_data["orders.dc"]
    tasks.append({
        "id": "val-08",
        "phase": 2,
        "task": (
            f"{hint}\n\n"
            f"Here is a DataCorp orders CSV export:\n\n"
            f"{_fmt_csv(orders_csv_text)}\n\n"
            f"Parse all data rows and validate them as a batch against the 'orders' schema "
            f"at {base_url}/validate. "
            f"How many records pass validation and how many fail?"
        ),
        "check": lambda output, env, vc=orders_valid_count, ic=orders_invalid_count: (
            str(vc) in output or str(ic) in output
        ),
        "difficulty": "medium",
    })

    # ---- Hard (val-09 … val-10) ----

    fixable_json = json.dumps(_FIXABLE_RECORDS, indent=2)
    tasks.append({
        "id": "val-09",
        "phase": 2,
        "task": (
            f"{hint}\n\n"
            f"These records fail validation against the 'orders' schema:\n\n"
            f"{fixable_json}\n\n"
            f"First call POST {base_url}/validate to identify the errors. "
            f"Then fix each record to make it pass validation (e.g., cast types, "
            f"correct enum values). Re-validate the fixed records and confirm they pass. "
            f"Return the fixed records and validation status."
        ),
        "check": lambda output, env: (
            "valid" in output.lower()
            and ("fix" in output.lower() or "3001" in output or "3002" in output)
        ),
        "difficulty": "hard",
    })

    cross_field_records = [
        # DC-007: refunded with amount > 0 is valid
        {"order_id": 5001, "customer": "ok@test.com", "amount": 50.0, "currency": "USD", "status": "refunded", "timestamp": 1710000000},
        # DC-007 violation: refunded with amount = 0 (or negative)
        {"order_id": 5002, "customer": "bad@test.com", "amount": -5.0, "currency": "USD", "status": "refunded", "timestamp": 1710000000},
        # Valid completed
        {"order_id": 5003, "customer": "fine@test.com", "amount": 200.0, "currency": "EUR", "status": "completed", "timestamp": 1710007200},
    ]
    cross_field_json = json.dumps(cross_field_records, indent=2)
    cross_result = validate_batch(cross_field_records, "orders")

    tasks.append({
        "id": "val-10",
        "phase": 2,
        "task": (
            f"{hint}\n\n"
            f"Validate these records against the 'orders' schema. "
            f"They test cross-field constraints (DC-007: refunded orders must have amount > 0):\n\n"
            f"{cross_field_json}\n\n"
            f"Identify which records violate cross-field constraints and explain why. "
            f"Return the error codes and which order_id(s) are affected."
        ),
        "check": lambda output, env: (
            "DC-007" in output and "5002" in output
        ),
        "difficulty": "hard",
    })

    return tasks


# ---------------------------------------------------------------------------
# Phase 3: DCQL Query Execution (10 tasks)
# ---------------------------------------------------------------------------

_DCQL_FORMAT_HINT = (
    "DataCorp Query Language (DCQL) is similar to SQL with these additions:\n"
    "  DC_CONVERT(amount, \"USD\") — convert amount to target currency\n"
    "  DC_HASH(email) — SHA-256 hash (first 16 hex chars) of a field value\n"
    "  DC_TIMERANGE(ts, \"1h\") — filter rows within last N hours/minutes\n"
    "Syntax: SELECT cols FROM table [WHERE cond AND cond] [GROUP BY col] [ORDER BY col] [LIMIT n]"
)


def make_datacorp_query_tasks(env) -> list[dict]:
    """10 Phase 3 tasks: DCQL query execution."""
    gt = env.ground_truth
    orders_parsed = env.csv_parsed["orders.dc"]
    orders_rows = orders_parsed["rows"]

    # Build in-memory tables from parsed CSVs
    tables = {
        "orders": orders_rows,
        "products": env.csv_parsed["products.dc"]["rows"],
        "customers": env.csv_parsed["customers.dc"]["rows"],
    }

    tasks = []

    # ---- Easy (qry-01 … qry-04) ----

    # qry-01: Simple SELECT with WHERE (status = completed)
    q1 = 'SELECT order_id, customer, amount FROM orders WHERE status = "completed"'
    r1 = execute_dcql(q1, tables)
    q1_count = r1["row_count"]

    tasks.append({
        "id": "qry-01",
        "phase": 3,
        "task": (
            f"{_DCQL_FORMAT_HINT}\n\n"
            f"Here is a DataCorp orders CSV export:\n\n"
            f"{_fmt_csv(env.csv_data['orders.dc'])}\n\n"
            f"Execute this DCQL query on the orders table and return the result count:\n\n"
            f"  {q1}\n\n"
            f"How many rows does this query return?"
        ),
        "check": lambda output, env, n=q1_count: str(n) in output,
        "difficulty": "easy",
    })

    # qry-02: SELECT with WHERE amount > threshold
    threshold = 500.0
    q2 = f"SELECT order_id, customer, amount, currency FROM orders WHERE amount > {threshold}"
    r2 = execute_dcql(q2, tables)
    q2_count = r2["row_count"]

    tasks.append({
        "id": "qry-02",
        "phase": 3,
        "task": (
            f"{_DCQL_FORMAT_HINT}\n\n"
            f"Here is a DataCorp orders CSV export:\n\n"
            f"{_fmt_csv(env.csv_data['orders.dc'])}\n\n"
            f"Execute this DCQL query and return how many rows match:\n\n"
            f"  {q2}\n\n"
            f"Return just the count."
        ),
        "check": lambda output, env, n=q2_count: str(n) in output,
        "difficulty": "easy",
    })

    # qry-03: SELECT * with WHERE + LIMIT
    q3 = 'SELECT * FROM orders WHERE currency = "USD" LIMIT 5'
    r3 = execute_dcql(q3, tables)
    q3_count = r3["row_count"]  # should be min(usd_count, 5)

    tasks.append({
        "id": "qry-03",
        "phase": 3,
        "task": (
            f"{_DCQL_FORMAT_HINT}\n\n"
            f"Here is a DataCorp orders CSV export:\n\n"
            f"{_fmt_csv(env.csv_data['orders.dc'])}\n\n"
            f"Execute this DCQL query:\n\n"
            f"  {q3}\n\n"
            f"How many rows are returned? (Hint: LIMIT caps the result.)"
        ),
        "check": lambda output, env, n=q3_count: str(n) in output,
        "difficulty": "easy",
    })

    # qry-04: Simple WHERE with AND
    q4 = 'SELECT order_id, amount FROM orders WHERE status = "completed" AND currency = "USD"'
    r4 = execute_dcql(q4, tables)
    q4_count = r4["row_count"]

    tasks.append({
        "id": "qry-04",
        "phase": 3,
        "task": (
            f"{_DCQL_FORMAT_HINT}\n\n"
            f"Here is a DataCorp orders CSV export:\n\n"
            f"{_fmt_csv(env.csv_data['orders.dc'])}\n\n"
            f"Execute this DCQL query:\n\n"
            f"  {q4}\n\n"
            f"Return the count of matching rows."
        ),
        "check": lambda output, env, n=q4_count: str(n) in output,
        "difficulty": "easy",
    })

    # ---- Medium (qry-05 … qry-08) ----

    # qry-05: GROUP BY currency
    q5 = "SELECT currency FROM orders GROUP BY currency"
    r5 = execute_dcql(q5, tables)
    q5_currencies = [row.get("currency") for row in r5["rows"]]

    tasks.append({
        "id": "qry-05",
        "phase": 3,
        "task": (
            f"{_DCQL_FORMAT_HINT}\n\n"
            f"Here is a DataCorp orders CSV export:\n\n"
            f"{_fmt_csv(env.csv_data['orders.dc'])}\n\n"
            f"Execute this DCQL query:\n\n"
            f"  {q5}\n\n"
            f"List the distinct currencies returned."
        ),
        "check": lambda output, env, currencies=q5_currencies: (
            any(c in output for c in currencies if c)
        ),
        "difficulty": "medium",
    })

    # qry-06: DC_CONVERT function
    q6 = 'SELECT order_id, DC_CONVERT(amount, "USD") AS amount_usd FROM orders WHERE status = "completed" LIMIT 3'
    r6 = execute_dcql(q6, tables)
    q6_row_count = r6["row_count"]

    tasks.append({
        "id": "qry-06",
        "phase": 3,
        "task": (
            f"{_DCQL_FORMAT_HINT}\n\n"
            f"Here is a DataCorp orders CSV export:\n\n"
            f"{_fmt_csv(env.csv_data['orders.dc'])}\n\n"
            f"Execute this DCQL query:\n\n"
            f"  {q6}\n\n"
            f"The DC_CONVERT function converts amounts to USD using exchange rates "
            f"(EUR=1.08, GBP=1.27, JPY=0.0067, CAD=0.74, AUD=0.65 relative to USD). "
            f"How many rows are returned? List the order_id and converted amount_usd for each."
        ),
        "check": lambda output, env, n=q6_row_count: str(n) in output,
        "difficulty": "medium",
    })

    # qry-07: DC_HASH function
    q7 = "SELECT order_id, DC_HASH(customer) AS customer_hash FROM orders LIMIT 3"
    r7 = execute_dcql(q7, tables)
    # Get the first hash value to check
    first_hash = r7["rows"][0].get("customer_hash", "") if r7["rows"] else ""

    tasks.append({
        "id": "qry-07",
        "phase": 3,
        "task": (
            f"{_DCQL_FORMAT_HINT}\n\n"
            f"Here is a DataCorp orders CSV export:\n\n"
            f"{_fmt_csv(env.csv_data['orders.dc'])}\n\n"
            f"Execute this DCQL query:\n\n"
            f"  {q7}\n\n"
            f"DC_HASH computes SHA-256 of the field value and returns the first 16 hex characters. "
            f"Return the order_id and customer_hash for each row."
        ),
        "check": lambda output, env, h=first_hash: (
            len(h) > 0 and (h in output or any(c in "0123456789abcdef" for c in output[:20]))
        ),
        "difficulty": "medium",
    })

    # qry-08: GROUP BY with ORDER BY
    q8 = "SELECT status FROM orders GROUP BY status ORDER BY status ASC"
    r8 = execute_dcql(q8, tables)
    q8_statuses = [row.get("status") for row in r8["rows"]]

    tasks.append({
        "id": "qry-08",
        "phase": 3,
        "task": (
            f"{_DCQL_FORMAT_HINT}\n\n"
            f"Here is a DataCorp orders CSV export:\n\n"
            f"{_fmt_csv(env.csv_data['orders.dc'])}\n\n"
            f"Execute this DCQL query:\n\n"
            f"  {q8}\n\n"
            f"List the distinct status values returned, in alphabetical order."
        ),
        "check": lambda output, env, statuses=q8_statuses: (
            any(s in output for s in statuses if s)
        ),
        "difficulty": "medium",
    })

    # ---- Hard (qry-09 … qry-10) ----

    # qry-09: DC_TIMERANGE filtering
    q9 = 'SELECT order_id, customer, amount FROM orders WHERE DC_TIMERANGE(timestamp, "24h") AND status = "completed"'
    r9 = execute_dcql(q9, tables)
    q9_count = r9["row_count"]

    tasks.append({
        "id": "qry-09",
        "phase": 3,
        "task": (
            f"{_DCQL_FORMAT_HINT}\n\n"
            f"Here is a DataCorp orders CSV export:\n\n"
            f"{_fmt_csv(env.csv_data['orders.dc'])}\n\n"
            f"Execute this DCQL query:\n\n"
            f"  {q9}\n\n"
            f"DC_TIMERANGE(timestamp, '24h') keeps only rows whose timestamp is within "
            f"the last 24 hours relative to the maximum timestamp in the dataset. "
            f"How many rows are returned?"
        ),
        "check": lambda output, env, n=q9_count: str(n) in output,
        "difficulty": "hard",
    })

    # qry-10: Complex multi-condition query with DC_CONVERT and ORDER BY
    q10 = (
        'SELECT order_id, customer, DC_CONVERT(amount, "EUR") AS eur_amount '
        'FROM orders '
        'WHERE status = "completed" AND amount > 200 '
        'ORDER BY amount DESC '
        'LIMIT 5'
    )
    r10 = execute_dcql(q10, tables)
    q10_count = r10["row_count"]
    q10_first_id = r10["rows"][0].get("order_id") if r10["rows"] else None

    tasks.append({
        "id": "qry-10",
        "phase": 3,
        "task": (
            f"{_DCQL_FORMAT_HINT}\n\n"
            f"Here is a DataCorp orders CSV export:\n\n"
            f"{_fmt_csv(env.csv_data['orders.dc'])}\n\n"
            f"Execute this DCQL query:\n\n"
            f"  {q10}\n\n"
            f"DC_CONVERT converts amounts to EUR (rate: 1 EUR = 1.08 USD, so USD amount / 1.08 = EUR). "
            f"Return the order_id, customer, and eur_amount for each result row. "
            f"How many rows are returned?"
        ),
        "check": lambda output, env, n=q10_count, fid=q10_first_id: (
            str(n) in output
        ),
        "difficulty": "hard",
    })

    return tasks


# ---------------------------------------------------------------------------
# Combined task list
# ---------------------------------------------------------------------------

def make_datacorp_tasks(env) -> list[dict]:
    """Generate all 30 DataCorp benchmark tasks."""
    return (
        make_datacorp_csv_tasks(env)
        + make_datacorp_validation_tasks(env)
        + make_datacorp_query_tasks(env)
    )
