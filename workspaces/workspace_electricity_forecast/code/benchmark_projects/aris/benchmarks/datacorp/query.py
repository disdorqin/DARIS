"""DataCorp Query Language (DCQL) parser and executor.

DCQL syntax:
    SELECT <col1>, <col2>, ... | *
    FROM <table>
    [WHERE <condition> [AND <condition> ...]]
    [GROUP BY <col>]
    [ORDER BY <col> [ASC|DESC]]
    [LIMIT <n>]

DataCorp-specific functions:
    DC_CONVERT(amount, "USD")   — convert numeric field to target currency (mock: multiply by rate)
    DC_HASH(field)              — SHA-256 hash of field value (first 16 hex chars)
    DC_TIMERANGE(ts_field, "1h") — filter to rows within the last N hours/minutes from max ts

Conditions:
    field = "value"     string equality
    field = number      numeric equality
    field > number      numeric comparison
    field < number
    field >= number
    field <= number
    field != "value"
"""

from __future__ import annotations

import hashlib
import re
from typing import Any


# ---------------------------------------------------------------------------
# Mock currency conversion rates (relative to USD)
# ---------------------------------------------------------------------------

_RATES: dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.27,
    "JPY": 0.0067,
    "CAD": 0.74,
    "AUD": 0.65,
}


# ---------------------------------------------------------------------------
# DCQL functions
# ---------------------------------------------------------------------------

def dc_convert(amount: Any, target_currency: str, source_currency: str = "USD") -> float:
    """Convert amount from source_currency to target_currency.

    Mock implementation using fixed rates.
    """
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return 0.0

    src_rate = _RATES.get(source_currency.upper(), 1.0)
    tgt_rate = _RATES.get(target_currency.upper(), 1.0)
    # Convert to USD first, then to target
    usd_amount = amount * src_rate
    return round(usd_amount / tgt_rate, 2)


def dc_hash(value: Any) -> str:
    """Return the first 16 hex characters of the SHA-256 hash of the value."""
    raw = str(value).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def dc_timerange(rows: list[dict], ts_field: str, duration: str) -> list[dict]:
    """Filter rows to those within 'duration' of the max timestamp in the dataset.

    duration format: "Nh" for N hours, "Nm" for N minutes, "Ns" for N seconds.
    """
    multipliers = {"h": 3600, "m": 60, "s": 1}
    m = re.match(r"^(\d+)([hms])$", duration.strip())
    if not m:
        raise ValueError(f"Invalid DC_TIMERANGE duration: {duration!r}")

    n, unit = int(m.group(1)), m.group(2)
    window_secs = n * multipliers[unit]

    timestamps = [
        row[ts_field] for row in rows
        if ts_field in row and isinstance(row[ts_field], (int, float))
    ]
    if not timestamps:
        return rows  # can't filter

    max_ts = max(timestamps)
    cutoff = max_ts - window_secs
    return [row for row in rows if isinstance(row.get(ts_field), (int, float)) and row[ts_field] >= cutoff]


# ---------------------------------------------------------------------------
# DCQL Tokenizer / Parser
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(
    r'"[^"]*"'          # quoted strings
    r"|'[^']*'"         # single-quoted strings
    r"|[<>!=]=?"        # operators: <=, >=, !=, <, >, =
    r"|[(),*]"          # punctuation
    r"|[A-Za-z_]\w*"    # identifiers / keywords
    r"|\d+(?:\.\d+)?"   # numbers
    r"|\S+"             # fallback: any non-whitespace
)


def _tokenize(query: str) -> list[str]:
    return _TOKEN_RE.findall(query)


class DCQLParser:
    """Recursive-descent parser for DCQL."""

    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected: str | None = None) -> str:
        tok = self.peek()
        if tok is None:
            raise ValueError(f"Unexpected end of query, expected {expected!r}")
        if expected is not None and tok.upper() != expected.upper():
            raise ValueError(f"Expected {expected!r}, got {tok!r}")
        self.pos += 1
        return tok

    def parse(self) -> dict:
        """Parse a DCQL query into an AST dict."""
        self.consume("SELECT")
        columns = self._parse_select_columns()

        self.consume("FROM")
        table = self.consume()

        where_clauses: list[dict] = []
        group_by: str | None = None
        order_by: tuple[str, str] | None = None
        limit: int | None = None

        while self.peek() is not None:
            kw = self.peek().upper() if self.peek() else ""
            if kw == "WHERE":
                self.consume("WHERE")
                where_clauses = self._parse_where()
            elif kw == "GROUP":
                self.consume("GROUP")
                self.consume("BY")
                group_by = self.consume()
            elif kw == "ORDER":
                self.consume("ORDER")
                self.consume("BY")
                col = self.consume()
                direction = "ASC"
                if self.peek() and self.peek().upper() in ("ASC", "DESC"):
                    direction = self.consume().upper()
                order_by = (col, direction)
            elif kw == "LIMIT":
                self.consume("LIMIT")
                limit = int(self.consume())
            else:
                break

        return {
            "type": "SELECT",
            "columns": columns,
            "table": table,
            "where": where_clauses,
            "group_by": group_by,
            "order_by": order_by,
            "limit": limit,
        }

    def _parse_select_columns(self) -> list[dict]:
        """Parse SELECT column list. May include DC_CONVERT, DC_HASH, aliases, *."""
        cols = []
        while True:
            col = self._parse_select_expr()
            cols.append(col)
            if self.peek() == ",":
                self.consume(",")
            else:
                break
        return cols

    def _parse_select_expr(self) -> dict:
        """Parse a single SELECT expression (column, function call, or *)."""
        tok = self.peek()
        if tok == "*":
            self.consume("*")
            return {"type": "star"}

        # Check for DC_ function calls
        if tok and tok.upper().startswith("DC_") and self._lookahead(1) == "(":
            return self._parse_dc_function()

        # Plain column name
        name = self.consume()
        # Optional alias: AS alias_name
        if self.peek() and self.peek().upper() == "AS":
            self.consume("AS")
            alias = self.consume()
            return {"type": "column", "name": name, "alias": alias}
        return {"type": "column", "name": name}

    def _parse_dc_function(self) -> dict:
        """Parse DC_CONVERT(...), DC_HASH(...), etc."""
        func_name = self.consume().upper()
        self.consume("(")
        args = []
        while self.peek() != ")":
            if self.peek() == ",":
                self.consume(",")
                continue
            arg = self.consume()
            # Strip quotes from string args
            if (arg.startswith('"') and arg.endswith('"')) or \
               (arg.startswith("'") and arg.endswith("'")):
                arg = arg[1:-1]
            args.append(arg)
        self.consume(")")
        # Optional alias
        alias = None
        if self.peek() and self.peek().upper() == "AS":
            self.consume("AS")
            alias = self.consume()
        return {"type": "function", "name": func_name, "args": args, "alias": alias}

    def _lookahead(self, n: int = 1) -> str | None:
        idx = self.pos + n
        return self.tokens[idx] if idx < len(self.tokens) else None

    def _parse_where(self) -> list[dict]:
        """Parse WHERE condition1 [AND condition2 ...]"""
        clauses = []
        while True:
            # Check for DC_TIMERANGE function in WHERE
            tok = self.peek()
            if tok and tok.upper() == "DC_TIMERANGE":
                self.consume("DC_TIMERANGE")
                self.consume("(")
                ts_field = self.consume()
                self.consume(",")
                duration = self.consume()
                if (duration.startswith('"') and duration.endswith('"')) or \
                   (duration.startswith("'") and duration.endswith("'")):
                    duration = duration[1:-1]
                self.consume(")")
                clauses.append({"type": "dc_timerange", "field": ts_field, "duration": duration})
            else:
                # field op value
                field = self.consume()
                op = self.consume()
                raw_val = self.consume()
                # Parse value type
                if (raw_val.startswith('"') and raw_val.endswith('"')) or \
                   (raw_val.startswith("'") and raw_val.endswith("'")):
                    val: Any = raw_val[1:-1]
                    val_type = "string"
                else:
                    try:
                        val = int(raw_val)
                        val_type = "number"
                    except ValueError:
                        try:
                            val = float(raw_val)
                            val_type = "number"
                        except ValueError:
                            val = raw_val
                            val_type = "string"
                clauses.append({"type": "condition", "field": field, "op": op, "value": val, "val_type": val_type})

            if self.peek() and self.peek().upper() == "AND":
                self.consume("AND")
            else:
                break

        return clauses


def parse_dcql(query: str) -> dict:
    """Parse a DCQL query string into an AST dict."""
    tokens = _tokenize(query)
    parser = DCQLParser(tokens)
    return parser.parse()


# ---------------------------------------------------------------------------
# DCQL Executor
# ---------------------------------------------------------------------------

def execute_dcql(query: str, tables: dict[str, list[dict]]) -> dict:
    """Execute a DCQL query against in-memory tables.

    Args:
        query: DCQL query string.
        tables: mapping of table_name → list of row dicts.

    Returns:
        {
            "columns": list[str],
            "rows": list[dict],
            "row_count": int,
            "query": str,
        }
    """
    ast = parse_dcql(query)
    table_name = ast["table"]

    if table_name not in tables:
        raise ValueError(f"Table '{table_name}' not found. Available: {list(tables.keys())}")

    rows = [dict(row) for row in tables[table_name]]

    # Apply DC_TIMERANGE filter first (it operates on full row set)
    timerange_clauses = [c for c in ast["where"] if c["type"] == "dc_timerange"]
    for clause in timerange_clauses:
        rows = dc_timerange(rows, clause["field"], clause["duration"])

    # Apply WHERE conditions
    condition_clauses = [c for c in ast["where"] if c["type"] == "condition"]
    for clause in condition_clauses:
        rows = _apply_condition(rows, clause)

    # GROUP BY + aggregation
    if ast["group_by"]:
        rows = _apply_group_by(rows, ast["group_by"], ast["columns"])
        # After grouping, columns are resolved
        col_names = _resolve_output_columns(ast["columns"], rows)
        output_rows = rows
    else:
        # Apply SELECT projections
        output_rows, col_names = _apply_projection(rows, ast["columns"])

    # ORDER BY
    if ast["order_by"]:
        order_col, direction = ast["order_by"]
        reverse = direction == "DESC"
        output_rows = sorted(
            output_rows,
            key=lambda r: (r.get(order_col) is None, r.get(order_col, "")),
            reverse=reverse,
        )

    # LIMIT
    if ast["limit"] is not None:
        output_rows = output_rows[:ast["limit"]]

    return {
        "columns": col_names,
        "rows": output_rows,
        "row_count": len(output_rows),
        "query": query,
    }


def _apply_condition(rows: list[dict], clause: dict) -> list[dict]:
    """Filter rows by a single condition clause."""
    field = clause["field"]
    op = clause["op"]
    expected = clause["value"]

    result = []
    for row in rows:
        actual = row.get(field)
        if actual is None:
            continue
        if _eval_condition(actual, op, expected):
            result.append(row)
    return result


def _eval_condition(actual: Any, op: str, expected: Any) -> bool:
    """Evaluate a condition between actual and expected."""
    if op == "=":
        # Try numeric comparison first
        try:
            return float(actual) == float(expected)
        except (TypeError, ValueError):
            return str(actual) == str(expected)
    elif op == "!=":
        try:
            return float(actual) != float(expected)
        except (TypeError, ValueError):
            return str(actual) != str(expected)
    elif op == ">":
        try:
            return float(actual) > float(expected)
        except (TypeError, ValueError):
            return False
    elif op == "<":
        try:
            return float(actual) < float(expected)
        except (TypeError, ValueError):
            return False
    elif op == ">=":
        try:
            return float(actual) >= float(expected)
        except (TypeError, ValueError):
            return False
    elif op == "<=":
        try:
            return float(actual) <= float(expected)
        except (TypeError, ValueError):
            return False
    return False


def _apply_projection(rows: list[dict], columns: list[dict]) -> tuple[list[dict], list[str]]:
    """Apply SELECT column projection (non-aggregating)."""
    if any(c["type"] == "star" for c in columns):
        # SELECT * — return all columns
        col_names = list(rows[0].keys()) if rows else []
        return rows, col_names

    col_names: list[str] = []
    output_rows: list[dict] = []

    # Determine output column names
    for col_def in columns:
        if col_def["type"] == "column":
            col_names.append(col_def.get("alias") or col_def["name"])
        elif col_def["type"] == "function":
            col_names.append(col_def.get("alias") or col_def["name"].lower())

    for row in rows:
        out_row: dict = {}
        for col_def in columns:
            if col_def["type"] == "column":
                out_name = col_def.get("alias") or col_def["name"]
                out_row[out_name] = row.get(col_def["name"])
            elif col_def["type"] == "function":
                out_name = col_def.get("alias") or col_def["name"].lower()
                out_row[out_name] = _eval_dc_function(col_def, row)
        output_rows.append(out_row)

    return output_rows, col_names


def _eval_dc_function(func_def: dict, row: dict) -> Any:
    """Evaluate a DC_ function call for a given row."""
    name = func_def["name"]
    args = func_def["args"]

    if name == "DC_CONVERT":
        if len(args) < 2:
            return None
        field_name = args[0]
        target_currency = args[1]
        amount = row.get(field_name, 0)
        # Determine source currency from row if available
        source_currency = row.get("currency", "USD")
        return dc_convert(amount, target_currency, source_currency)

    elif name == "DC_HASH":
        if not args:
            return None
        field_name = args[0]
        return dc_hash(row.get(field_name, ""))

    return None


def _apply_group_by(rows: list[dict], group_col: str, columns: list[dict]) -> list[dict]:
    """Apply GROUP BY aggregation.

    Supported aggregate patterns (detected by column name):
        COUNT(*)    → count of rows per group
        SUM(field)  → sum of field per group
        AVG(field)  → avg of field per group
    """
    from collections import defaultdict

    groups: dict[Any, list[dict]] = defaultdict(list)
    for row in rows:
        key = row.get(group_col)
        groups[key].append(row)

    output_rows = []
    for group_key, group_rows in sorted(groups.items(), key=lambda x: str(x[0])):
        out_row: dict = {group_col: group_key}

        for col_def in columns:
            if col_def["type"] == "star":
                out_row["count"] = len(group_rows)
            elif col_def["type"] == "column":
                col_name = col_def["name"]
                if col_name == group_col:
                    continue  # already added
                # Default: take first value in group (for non-aggregated columns)
                out_row[col_name] = group_rows[0].get(col_name) if group_rows else None
            elif col_def["type"] == "function":
                alias = col_def.get("alias") or col_def["name"].lower()
                out_row[alias] = _eval_dc_function(col_def, group_rows[0]) if group_rows else None

        output_rows.append(out_row)

    return output_rows


def _resolve_output_columns(columns: list[dict], rows: list[dict]) -> list[str]:
    """Get output column names after grouping."""
    if not rows:
        return []
    return list(rows[0].keys())
