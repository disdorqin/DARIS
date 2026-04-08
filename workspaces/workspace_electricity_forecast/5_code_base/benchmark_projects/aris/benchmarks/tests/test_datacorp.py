"""Tests for the DataCorp benchmark modules."""

from __future__ import annotations

import os
import time

import pytest

from benchmarks.datacorp.csv_format import (
    generate_orders_csv,
    generate_products_csv,
    generate_customers_csv,
    parse_datacorp_csv,
    gt_row_count,
    gt_column_values,
    gt_filter_rows,
    gt_sum_by_group,
    gt_detect_duplicates,
    gt_pivot_status_by_currency,
    gt_running_average,
    gt_join_csvs,
    CURRENCIES,
    STATUSES,
)
from benchmarks.datacorp.validation_api import (
    SCHEMAS,
    validate_record,
    validate_batch,
    auto_fix_record,
    create_validation_app,
    start_validation_server,
    stop_validation_server,
)
from benchmarks.datacorp.query import (
    parse_dcql,
    execute_dcql,
    dc_convert,
    dc_hash,
    dc_timerange,
)
from benchmarks.datacorp.fixtures import DataCorpEnv, generate
from benchmarks.tasks.datacorp_tasks import (
    make_datacorp_csv_tasks,
    make_datacorp_validation_tasks,
    make_datacorp_query_tasks,
    make_datacorp_tasks,
)


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture(scope="module")
def env_seed42():
    env = generate(42)
    yield env
    env.cleanup()


@pytest.fixture(scope="module")
def env_seed42_b():
    env = generate(42)
    yield env
    env.cleanup()


@pytest.fixture(scope="module")
def env_seed99():
    env = generate(99)
    yield env
    env.cleanup()


@pytest.fixture(scope="module")
def orders_text_42():
    return generate_orders_csv(42, count=50)


@pytest.fixture(scope="module")
def orders_parsed_42(orders_text_42):
    return parse_datacorp_csv(orders_text_42)


@pytest.fixture(scope="module")
def validation_server():
    """Start a validation server on a test port."""
    port = 19099
    thread = start_validation_server(port=port)
    time.sleep(0.1)
    yield port
    stop_validation_server(thread)


# ===========================================================================
# csv_format.py tests
# ===========================================================================

class TestGenerateOrdersCsv:
    def test_returns_string(self):
        text = generate_orders_csv(42, count=10)
        assert isinstance(text, str)

    def test_has_two_header_lines(self):
        text = generate_orders_csv(42, count=10)
        lines = text.strip().splitlines()
        header_lines = [l for l in lines if l.startswith("##")]
        assert len(header_lines) == 2

    def test_first_header_has_schema(self):
        text = generate_orders_csv(42, count=10, schema="orders")
        assert "schema=orders" in text

    def test_first_header_has_exported(self):
        text = generate_orders_csv(42, count=10, exported_date="2024-03-01")
        assert "exported=2024-03-01" in text

    def test_second_header_has_columns(self):
        text = generate_orders_csv(42, count=10)
        assert "## columns:" in text
        assert "order_id" in text
        assert "customer" in text
        assert "amount" in text

    def test_correct_row_count(self):
        text = generate_orders_csv(42, count=20)
        lines = [l for l in text.strip().splitlines() if not l.startswith("##")]
        assert len(lines) == 20

    def test_pipe_delimiter_in_rows(self):
        text = generate_orders_csv(42, count=5)
        data_lines = [l for l in text.strip().splitlines() if not l.startswith("##")]
        for line in data_lines:
            assert "|" in line

    def test_deterministic_with_same_seed(self):
        t1 = generate_orders_csv(42, count=10)
        t2 = generate_orders_csv(42, count=10)
        assert t1 == t2

    def test_different_seeds_differ(self):
        t1 = generate_orders_csv(42, count=10)
        t2 = generate_orders_csv(99, count=10)
        assert t1 != t2


class TestGenerateProductsCsv:
    def test_returns_string(self):
        text = generate_products_csv(42)
        assert isinstance(text, str)

    def test_schema_is_products(self):
        text = generate_products_csv(42, schema="products")
        assert "schema=products" in text

    def test_has_product_columns(self):
        text = generate_products_csv(42)
        assert "product_id" in text
        assert "price" in text
        assert "category" in text


class TestGenerateCustomersCsv:
    def test_returns_string(self):
        text = generate_customers_csv(42)
        assert isinstance(text, str)

    def test_has_customer_columns(self):
        text = generate_customers_csv(42)
        assert "customer_id" in text
        assert "email" in text
        assert "tier" in text


class TestParseDatacorpCsv:
    def test_returns_dict(self, orders_parsed_42):
        assert isinstance(orders_parsed_42, dict)

    def test_has_required_keys(self, orders_parsed_42):
        assert "metadata" in orders_parsed_42
        assert "columns" in orders_parsed_42
        assert "rows" in orders_parsed_42
        assert "raw_rows" in orders_parsed_42

    def test_metadata_has_schema(self, orders_parsed_42):
        assert "schema" in orders_parsed_42["metadata"]
        assert orders_parsed_42["metadata"]["schema"] == "orders"

    def test_columns_parsed(self, orders_parsed_42):
        cols = orders_parsed_42["columns"]
        assert "order_id" in cols
        assert "customer" in cols
        assert "amount" in cols
        assert "currency" in cols
        assert "status" in cols
        assert "timestamp" in cols

    def test_row_count_matches_generated(self, orders_parsed_42):
        assert len(orders_parsed_42["rows"]) == 50

    def test_rows_are_dicts(self, orders_parsed_42):
        for row in orders_parsed_42["rows"]:
            assert isinstance(row, dict)

    def test_amount_is_float(self, orders_parsed_42):
        for row in orders_parsed_42["rows"]:
            assert isinstance(row["amount"], float)

    def test_order_id_is_int(self, orders_parsed_42):
        for row in orders_parsed_42["rows"]:
            assert isinstance(row["order_id"], int)

    def test_timestamp_is_int(self, orders_parsed_42):
        for row in orders_parsed_42["rows"]:
            assert isinstance(row["timestamp"], int)

    def test_currency_is_valid(self, orders_parsed_42):
        for row in orders_parsed_42["rows"]:
            assert row["currency"] in CURRENCIES

    def test_status_is_valid(self, orders_parsed_42):
        for row in orders_parsed_42["rows"]:
            assert row["status"] in STATUSES

    def test_parse_is_reversible(self, orders_text_42, orders_parsed_42):
        """Re-parsing the generated text yields same result."""
        reparsed = parse_datacorp_csv(orders_text_42)
        assert reparsed["columns"] == orders_parsed_42["columns"]
        assert reparsed["rows"] == orders_parsed_42["rows"]


class TestGroundTruthHelpers:
    def test_gt_row_count(self, orders_parsed_42):
        assert gt_row_count(orders_parsed_42) == 50

    def test_gt_column_values_currency(self, orders_parsed_42):
        vals = gt_column_values(orders_parsed_42, "currency")
        assert len(vals) == 50
        assert all(v in CURRENCIES for v in vals)

    def test_gt_filter_rows_completed(self, orders_parsed_42):
        completed = gt_filter_rows(orders_parsed_42, "status", "completed")
        assert all(r["status"] == "completed" for r in completed)

    def test_gt_sum_by_group_currency(self, orders_parsed_42):
        sums = gt_sum_by_group(orders_parsed_42, "amount", "currency")
        assert isinstance(sums, dict)
        assert all(isinstance(v, float) for v in sums.values())

    def test_gt_sum_is_consistent(self, orders_parsed_42):
        sums = gt_sum_by_group(orders_parsed_42, "amount", "currency")
        amounts = gt_column_values(orders_parsed_42, "amount")
        assert abs(sum(sums.values()) - sum(amounts)) < 0.01

    def test_gt_detect_duplicates(self, orders_parsed_42):
        dups = gt_detect_duplicates(orders_parsed_42, "customer")
        assert isinstance(dups, list)
        # Some customers will appear more than once in 50 orders from 16 customers

    def test_gt_pivot_status_by_currency(self, orders_parsed_42):
        pivot = gt_pivot_status_by_currency(orders_parsed_42)
        assert isinstance(pivot, dict)
        # All currencies should map to a dict of status -> count
        for currency, status_counts in pivot.items():
            assert currency in CURRENCIES
            assert isinstance(status_counts, dict)

    def test_gt_pivot_counts_sum_to_total(self, orders_parsed_42):
        pivot = gt_pivot_status_by_currency(orders_parsed_42)
        total = sum(count for sc in pivot.values() for count in sc.values())
        assert total == gt_row_count(orders_parsed_42)

    def test_gt_running_average_length(self, orders_parsed_42):
        running = gt_running_average(orders_parsed_42, "amount")
        assert len(running) == gt_row_count(orders_parsed_42)

    def test_gt_running_average_final(self, orders_parsed_42):
        running = gt_running_average(orders_parsed_42, "amount")
        amounts = gt_column_values(orders_parsed_42, "amount")
        expected_avg = round(sum(amounts) / len(amounts), 4)
        assert abs(running[-1] - expected_avg) < 0.01

    def test_gt_join_csvs(self):
        left = parse_datacorp_csv(generate_orders_csv(42, count=10))
        right = parse_datacorp_csv(generate_customers_csv(42))
        joined = gt_join_csvs(left, right, "customer", "email")
        assert isinstance(joined, list)
        for row in joined:
            assert "customer" in row
            assert "r_email" in row


# ===========================================================================
# validation_api.py tests
# ===========================================================================

class TestSchemas:
    def test_schemas_is_dict(self):
        assert isinstance(SCHEMAS, dict)

    def test_has_orders_schema(self):
        assert "orders" in SCHEMAS

    def test_has_products_schema(self):
        assert "products" in SCHEMAS

    def test_has_customers_schema(self):
        assert "customers" in SCHEMAS

    def test_orders_schema_has_fields(self):
        fields = SCHEMAS["orders"]["fields"]
        assert "order_id" in fields
        assert "customer" in fields
        assert "amount" in fields
        assert "currency" in fields
        assert "status" in fields
        assert "timestamp" in fields


class TestValidateRecord:
    def _good_record(self):
        return {
            "order_id": 1,
            "customer": "test@example.com",
            "amount": 100.0,
            "currency": "USD",
            "status": "completed",
            "timestamp": 1710000000,
        }

    def test_valid_record_has_no_errors(self):
        errors = validate_record(self._good_record(), SCHEMAS["orders"])
        assert errors == []

    def test_missing_required_field_dc001(self):
        rec = self._good_record()
        del rec["timestamp"]
        errors = validate_record(rec, SCHEMAS["orders"])
        codes = [e["code"] for e in errors]
        assert "DC-001" in codes

    def test_invalid_currency_dc004(self):
        rec = self._good_record()
        rec["currency"] = "XYZ"
        errors = validate_record(rec, SCHEMAS["orders"])
        codes = [e["code"] for e in errors]
        assert "DC-004" in codes

    def test_invalid_status_dc004(self):
        rec = self._good_record()
        rec["status"] = "shipped"
        errors = validate_record(rec, SCHEMAS["orders"])
        codes = [e["code"] for e in errors]
        assert "DC-004" in codes

    def test_negative_amount_dc003(self):
        rec = self._good_record()
        rec["amount"] = -10.0
        errors = validate_record(rec, SCHEMAS["orders"])
        codes = [e["code"] for e in errors]
        assert "DC-003" in codes

    def test_refunded_negative_amount_dc007(self):
        rec = self._good_record()
        rec["status"] = "refunded"
        rec["amount"] = -5.0
        errors = validate_record(rec, SCHEMAS["orders"])
        codes = [e["code"] for e in errors]
        assert "DC-007" in codes

    def test_refunded_positive_amount_no_dc007(self):
        rec = self._good_record()
        rec["status"] = "refunded"
        rec["amount"] = 50.0
        errors = validate_record(rec, SCHEMAS["orders"])
        codes = [e["code"] for e in errors]
        assert "DC-007" not in codes


class TestValidateBatch:
    def _valid_record(self, oid: int) -> dict:
        return {
            "order_id": oid,
            "customer": f"user{oid}@example.com",
            "amount": float(oid * 10),
            "currency": "USD",
            "status": "completed",
            "timestamp": 1710000000 + oid,
        }

    def test_all_valid_batch(self):
        records = [self._valid_record(i) for i in range(1, 6)]
        result = validate_batch(records, "orders")
        assert result["valid_count"] == 5
        assert result["invalid_count"] == 0

    def test_invalid_schema_returns_error(self):
        result = validate_batch([], "nonexistent_schema")
        assert "error" in result
        assert "DC-010" in result.get("code", "")

    def test_batch_with_invalid_records(self):
        records = [
            self._valid_record(1),
            {"order_id": 2, "customer": "bad", "amount": -5.0, "currency": "INVALID", "status": "foo", "timestamp": 1},
        ]
        result = validate_batch(records, "orders")
        assert result["valid_count"] == 1
        assert result["invalid_count"] == 1

    def test_duplicate_primary_key_dc008(self):
        records = [
            self._valid_record(100),
            self._valid_record(100),  # same order_id
        ]
        result = validate_batch(records, "orders")
        assert result["invalid_count"] >= 1
        assert "DC-008" in result["error_summary"]

    def test_error_summary_is_dict(self):
        records = [{"order_id": 9, "customer": "bad@x.com", "amount": "nope", "currency": "ZZZ", "status": "foo"}]
        result = validate_batch(records, "orders")
        assert isinstance(result["error_summary"], dict)

    def test_returns_correct_keys(self):
        result = validate_batch([self._valid_record(1)], "orders")
        assert "schema" in result
        assert "total" in result
        assert "valid_count" in result
        assert "invalid_count" in result
        assert "valid" in result
        assert "invalid" in result
        assert "error_summary" in result

    def test_total_matches_input_count(self):
        records = [self._valid_record(i) for i in range(1, 8)]
        result = validate_batch(records, "orders")
        assert result["total"] == 7


class TestAutoFixRecord:
    def test_fixes_string_amount(self):
        record = {
            "order_id": 1,
            "customer": "a@b.com",
            "amount": "150.50",
            "currency": "USD",
            "status": "completed",
            "timestamp": 1710000000,
        }
        fixed, fixes = auto_fix_record(record, "orders")
        assert isinstance(fixed["amount"], float)
        assert len(fixes) > 0

    def test_returns_tuple(self):
        record = {"order_id": 1, "customer": "a@b.com", "amount": 10.0, "currency": "USD",
                  "status": "completed", "timestamp": 1710000000}
        result = auto_fix_record(record, "orders")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_unknown_schema_returns_unchanged(self):
        record = {"field": "value"}
        fixed, fixes = auto_fix_record(record, "unknown_schema")
        assert fixed == record
        assert fixes == []

    def test_clamps_negative_amount(self):
        record = {
            "order_id": 1,
            "customer": "a@b.com",
            "amount": -50.0,
            "currency": "USD",
            "status": "completed",
            "timestamp": 1710000000,
        }
        fixed, fixes = auto_fix_record(record, "orders")
        assert fixed["amount"] >= 0.01


class TestValidationApiServer:
    def test_server_starts(self, validation_server):
        import urllib.request
        url = f"http://127.0.0.1:{validation_server}/schemas"
        resp = urllib.request.urlopen(url, timeout=3)
        assert resp.status == 200

    def test_list_schemas_endpoint(self, validation_server):
        import json, urllib.request
        url = f"http://127.0.0.1:{validation_server}/schemas"
        resp = urllib.request.urlopen(url, timeout=3)
        data = json.loads(resp.read())
        assert "orders" in data
        assert "products" in data
        assert "customers" in data

    def test_get_schema_endpoint(self, validation_server):
        import json, urllib.request
        url = f"http://127.0.0.1:{validation_server}/schemas/orders"
        resp = urllib.request.urlopen(url, timeout=3)
        data = json.loads(resp.read())
        assert data["name"] == "orders"
        assert "fields" in data

    def test_get_unknown_schema_returns_404(self, validation_server):
        import urllib.request, urllib.error
        url = f"http://127.0.0.1:{validation_server}/schemas/nonexistent"
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(url, timeout=3)
        assert exc_info.value.code == 404

    def test_validate_endpoint_valid_record(self, validation_server):
        import json, urllib.request
        record = {
            "order_id": 1,
            "customer": "ok@test.com",
            "amount": 100.0,
            "currency": "USD",
            "status": "completed",
            "timestamp": 1710000000,
        }
        body = json.dumps({"records": [record], "schema": "orders"}).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{validation_server}/validate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=3)
        data = json.loads(resp.read())
        assert data["valid_count"] == 1
        assert data["invalid_count"] == 0

    def test_validate_endpoint_invalid_record(self, validation_server):
        import json, urllib.request
        record = {"order_id": 2, "customer": "bad", "amount": -1, "currency": "ZZZ",
                  "status": "shipped", "timestamp": 1710000000}
        body = json.dumps({"records": [record], "schema": "orders"}).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{validation_server}/validate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=3)
        data = json.loads(resp.read())
        assert data["invalid_count"] == 1


# ===========================================================================
# query.py tests
# ===========================================================================

SAMPLE_ORDERS = [
    {"order_id": 1, "customer": "alice@corp.com", "amount": 450.0, "currency": "USD", "status": "completed", "timestamp": 1710000000},
    {"order_id": 2, "customer": "bob@corp.com", "amount": 89.99, "currency": "EUR", "status": "pending", "timestamp": 1710003600},
    {"order_id": 3, "customer": "carol@corp.com", "amount": 1200.0, "currency": "GBP", "status": "completed", "timestamp": 1710007200},
    {"order_id": 4, "customer": "dave@corp.com", "amount": 50.0, "currency": "USD", "status": "failed", "timestamp": 1710010800},
    {"order_id": 5, "customer": "eve@corp.com", "amount": 750.0, "currency": "EUR", "status": "completed", "timestamp": 1710014400},
]

SAMPLE_TABLES = {"orders": SAMPLE_ORDERS}


class TestDcConvert:
    def test_usd_to_usd_unchanged(self):
        assert dc_convert(100.0, "USD", "USD") == 100.0

    def test_usd_to_eur(self):
        # 100 USD → 100/1.08 EUR ≈ 92.59
        result = dc_convert(100.0, "EUR", "USD")
        assert abs(result - 92.59) < 0.1

    def test_eur_to_usd(self):
        # 100 EUR * 1.08 = 108 USD
        result = dc_convert(100.0, "USD", "EUR")
        assert abs(result - 108.0) < 0.1

    def test_invalid_amount_returns_zero(self):
        assert dc_convert("not-a-number", "USD") == 0.0

    def test_unknown_currency_defaults_to_rate_1(self):
        # Unknown currency defaults rate to 1.0
        result = dc_convert(100.0, "UNKNOWN", "USD")
        assert isinstance(result, float)


class TestDcHash:
    def test_returns_16_hex_chars(self):
        result = dc_hash("alice@corp.com")
        assert len(result) == 16
        assert all(c in "0123456789abcdef" for c in result)

    def test_same_input_same_hash(self):
        assert dc_hash("test@example.com") == dc_hash("test@example.com")

    def test_different_inputs_different_hashes(self):
        assert dc_hash("alice@corp.com") != dc_hash("bob@corp.com")

    def test_handles_non_string(self):
        result = dc_hash(12345)
        assert len(result) == 16


class TestDcTimerange:
    def test_returns_subset(self):
        rows = SAMPLE_ORDERS
        result = dc_timerange(rows, "timestamp", "6h")
        assert len(result) <= len(rows)
        assert len(result) > 0

    def test_invalid_duration_raises(self):
        with pytest.raises(ValueError):
            dc_timerange(SAMPLE_ORDERS, "timestamp", "bad_format")

    def test_all_rows_in_huge_window(self):
        result = dc_timerange(SAMPLE_ORDERS, "timestamp", "9999h")
        assert len(result) == len(SAMPLE_ORDERS)

    def test_no_rows_in_zero_window(self):
        result = dc_timerange(SAMPLE_ORDERS, "timestamp", "0h")
        # Only the last row (at max_ts) should remain since cutoff == max_ts
        assert len(result) <= 1


class TestParseDcql:
    def test_simple_select(self):
        ast = parse_dcql("SELECT order_id, customer FROM orders")
        assert ast["type"] == "SELECT"
        assert ast["table"] == "orders"
        assert len(ast["columns"]) == 2

    def test_select_star(self):
        ast = parse_dcql("SELECT * FROM orders")
        assert any(c["type"] == "star" for c in ast["columns"])

    def test_where_clause(self):
        ast = parse_dcql('SELECT * FROM orders WHERE status = "completed"')
        assert len(ast["where"]) == 1
        assert ast["where"][0]["field"] == "status"
        assert ast["where"][0]["op"] == "="
        assert ast["where"][0]["value"] == "completed"

    def test_where_numeric(self):
        ast = parse_dcql("SELECT * FROM orders WHERE amount > 100")
        cond = ast["where"][0]
        assert cond["field"] == "amount"
        assert cond["op"] == ">"
        assert cond["value"] == 100

    def test_where_and(self):
        ast = parse_dcql('SELECT * FROM orders WHERE status = "completed" AND amount > 100')
        assert len(ast["where"]) == 2

    def test_group_by(self):
        ast = parse_dcql("SELECT currency FROM orders GROUP BY currency")
        assert ast["group_by"] == "currency"

    def test_order_by_asc(self):
        ast = parse_dcql("SELECT * FROM orders ORDER BY amount ASC")
        assert ast["order_by"] == ("amount", "ASC")

    def test_order_by_desc(self):
        ast = parse_dcql("SELECT * FROM orders ORDER BY amount DESC")
        assert ast["order_by"] == ("amount", "DESC")

    def test_limit(self):
        ast = parse_dcql("SELECT * FROM orders LIMIT 5")
        assert ast["limit"] == 5

    def test_dc_convert_function(self):
        ast = parse_dcql('SELECT DC_CONVERT(amount, "USD") FROM orders')
        col = ast["columns"][0]
        assert col["type"] == "function"
        assert col["name"] == "DC_CONVERT"

    def test_dc_hash_function(self):
        ast = parse_dcql("SELECT DC_HASH(customer) FROM orders")
        col = ast["columns"][0]
        assert col["type"] == "function"
        assert col["name"] == "DC_HASH"

    def test_dc_timerange_in_where(self):
        ast = parse_dcql('SELECT * FROM orders WHERE DC_TIMERANGE(timestamp, "1h")')
        assert ast["where"][0]["type"] == "dc_timerange"
        assert ast["where"][0]["field"] == "timestamp"
        assert ast["where"][0]["duration"] == "1h"

    def test_alias_with_as(self):
        ast = parse_dcql('SELECT DC_CONVERT(amount, "USD") AS amount_usd FROM orders')
        col = ast["columns"][0]
        assert col.get("alias") == "amount_usd"

    def test_missing_from_raises(self):
        with pytest.raises((ValueError, IndexError, StopIteration)):
            parse_dcql("SELECT order_id")


class TestExecuteDcql:
    def test_select_star(self):
        result = execute_dcql("SELECT * FROM orders", SAMPLE_TABLES)
        assert result["row_count"] == 5

    def test_select_specific_columns(self):
        result = execute_dcql("SELECT order_id, customer FROM orders", SAMPLE_TABLES)
        assert result["row_count"] == 5
        for row in result["rows"]:
            assert "order_id" in row
            assert "customer" in row
            assert "amount" not in row

    def test_where_status_completed(self):
        result = execute_dcql('SELECT * FROM orders WHERE status = "completed"', SAMPLE_TABLES)
        assert result["row_count"] == 3
        for row in result["rows"]:
            assert row["status"] == "completed"

    def test_where_amount_gt(self):
        result = execute_dcql("SELECT * FROM orders WHERE amount > 100", SAMPLE_TABLES)
        for row in result["rows"]:
            assert row["amount"] > 100

    def test_where_and(self):
        result = execute_dcql(
            'SELECT * FROM orders WHERE status = "completed" AND amount > 500',
            SAMPLE_TABLES,
        )
        for row in result["rows"]:
            assert row["status"] == "completed"
            assert row["amount"] > 500

    def test_limit(self):
        result = execute_dcql("SELECT * FROM orders LIMIT 2", SAMPLE_TABLES)
        assert result["row_count"] == 2

    def test_group_by_currency(self):
        result = execute_dcql("SELECT currency FROM orders GROUP BY currency", SAMPLE_TABLES)
        currencies = {row["currency"] for row in result["rows"]}
        assert currencies == {"USD", "EUR", "GBP"}

    def test_order_by_amount_asc(self):
        result = execute_dcql("SELECT * FROM orders ORDER BY amount ASC", SAMPLE_TABLES)
        amounts = [row["amount"] for row in result["rows"]]
        assert amounts == sorted(amounts)

    def test_order_by_amount_desc(self):
        result = execute_dcql("SELECT * FROM orders ORDER BY amount DESC", SAMPLE_TABLES)
        amounts = [row["amount"] for row in result["rows"]]
        assert amounts == sorted(amounts, reverse=True)

    def test_dc_convert_column(self):
        result = execute_dcql(
            'SELECT order_id, DC_CONVERT(amount, "EUR") AS eur_amount FROM orders WHERE order_id = 1',
            SAMPLE_TABLES,
        )
        assert result["row_count"] == 1
        eur = result["rows"][0]["eur_amount"]
        # 450 USD → 450/1.08 ≈ 416.67 EUR
        assert isinstance(eur, float)
        assert abs(eur - 416.67) < 1.0

    def test_dc_hash_column(self):
        result = execute_dcql(
            "SELECT order_id, DC_HASH(customer) AS h FROM orders LIMIT 1",
            SAMPLE_TABLES,
        )
        assert result["row_count"] == 1
        h = result["rows"][0]["h"]
        assert len(h) == 16
        assert all(c in "0123456789abcdef" for c in h)

    def test_dc_timerange_filter(self):
        result = execute_dcql(
            'SELECT * FROM orders WHERE DC_TIMERANGE(timestamp, "6h")',
            SAMPLE_TABLES,
        )
        # 6h = 21600 seconds; max_ts=1710014400, cutoff=1710014400-21600=1709992800
        # All 5 rows are within 6h of max (range is only 4h = 14400s)
        assert result["row_count"] == 5

    def test_unknown_table_raises(self):
        with pytest.raises(ValueError):
            execute_dcql("SELECT * FROM nonexistent", SAMPLE_TABLES)

    def test_result_has_required_keys(self):
        result = execute_dcql("SELECT * FROM orders LIMIT 1", SAMPLE_TABLES)
        assert "columns" in result
        assert "rows" in result
        assert "row_count" in result
        assert "query" in result


# ===========================================================================
# fixtures.py tests
# ===========================================================================

class TestDataCorpEnvGenerate:
    def test_returns_datacorp_env(self, env_seed42):
        assert isinstance(env_seed42, DataCorpEnv)

    def test_csv_data_is_dict(self, env_seed42):
        assert isinstance(env_seed42.csv_data, dict)

    def test_csv_data_has_three_files(self, env_seed42):
        assert "orders.dc" in env_seed42.csv_data
        assert "products.dc" in env_seed42.csv_data
        assert "customers.dc" in env_seed42.csv_data

    def test_csv_file_paths_exist(self, env_seed42):
        for filename, path in env_seed42.csv_file_paths.items():
            assert os.path.isfile(path), f"File not found: {path}"

    def test_csv_file_content_matches(self, env_seed42):
        for filename, text in env_seed42.csv_data.items():
            path = env_seed42.csv_file_paths[filename]
            with open(path, "r", encoding="utf-8") as f:
                on_disk = f.read()
            assert on_disk == text

    def test_csv_parsed_is_dict(self, env_seed42):
        assert isinstance(env_seed42.csv_parsed, dict)
        assert "orders.dc" in env_seed42.csv_parsed

    def test_schemas_is_dict(self, env_seed42):
        assert isinstance(env_seed42.schemas, dict)
        assert "orders" in env_seed42.schemas

    def test_validation_port_stored(self, env_seed42):
        assert env_seed42.validation_port == 19080

    def test_ground_truth_is_dict(self, env_seed42):
        assert isinstance(env_seed42.ground_truth, dict)


class TestGroundTruthKeys:
    EXPECTED_KEYS = {
        "order_count",
        "product_count",
        "customer_count",
        "completed_order_count",
        "sum_by_currency",
        "total_amount",
        "avg_amount",
        "pivot_status_by_currency",
        "running_avg_amounts",
        "duplicate_customers",
        "usd_order_count",
        "validation_valid_count",
        "validation_invalid_count",
        "validation_error_summary",
        "schema_names",
    }

    def test_has_all_expected_keys(self, env_seed42):
        missing = self.EXPECTED_KEYS - set(env_seed42.ground_truth.keys())
        assert missing == set(), f"Missing keys: {missing}"

    def test_order_count_is_int(self, env_seed42):
        assert isinstance(env_seed42.ground_truth["order_count"], int)
        assert env_seed42.ground_truth["order_count"] == 50

    def test_sum_by_currency_is_dict(self, env_seed42):
        assert isinstance(env_seed42.ground_truth["sum_by_currency"], dict)

    def test_total_amount_is_float(self, env_seed42):
        assert isinstance(env_seed42.ground_truth["total_amount"], (int, float))

    def test_total_matches_sum_by_currency(self, env_seed42):
        gt = env_seed42.ground_truth
        assert abs(gt["total_amount"] - sum(gt["sum_by_currency"].values())) < 0.1

    def test_schema_names_contains_orders(self, env_seed42):
        assert "orders" in env_seed42.ground_truth["schema_names"]


class TestDeterminism:
    def test_csv_data_is_deterministic(self, env_seed42, env_seed42_b):
        assert env_seed42.csv_data == env_seed42_b.csv_data

    def test_ground_truth_is_deterministic(self, env_seed42, env_seed42_b):
        assert env_seed42.ground_truth == env_seed42_b.ground_truth

    def test_different_seeds_differ(self, env_seed42, env_seed99):
        assert env_seed42.csv_data["orders.dc"] != env_seed99.csv_data["orders.dc"]


class TestCleanup:
    def test_cleanup_removes_tmpdir(self):
        env = generate(seed=7)
        tmpdir = env._tmpdir
        assert os.path.exists(tmpdir)
        env.cleanup()
        assert not os.path.exists(tmpdir)

    def test_cleanup_idempotent(self):
        env = generate(seed=8)
        env.cleanup()
        env.cleanup()  # should not raise


# ===========================================================================
# Task tests
# ===========================================================================

class TestCsvTasks:
    @pytest.fixture(scope="class")
    def tasks(self, env_seed42):
        return make_datacorp_csv_tasks(env_seed42)

    def test_returns_list(self, tasks):
        assert isinstance(tasks, list)

    def test_correct_count(self, tasks):
        assert len(tasks) == 10

    def test_task_ids(self, tasks):
        ids = [t["id"] for t in tasks]
        assert ids == [f"csv-{i:02d}" for i in range(1, 11)]

    def test_all_phase_1(self, tasks):
        assert all(t["phase"] == 1 for t in tasks)

    def test_difficulties_present(self, tasks):
        diffs = {t["difficulty"] for t in tasks}
        assert "easy" in diffs
        assert "medium" in diffs
        assert "hard" in diffs

    def test_check_is_callable(self, tasks):
        for t in tasks:
            assert callable(t["check"])

    def test_task_has_task_string(self, tasks):
        for t in tasks:
            assert isinstance(t["task"], str)
            assert len(t["task"]) > 10

    def test_csv01_check_correct(self, tasks, env_seed42):
        t = tasks[0]  # csv-01: row count
        n = env_seed42.ground_truth["order_count"]
        assert t["check"](str(n), env_seed42) is True

    def test_csv01_check_wrong(self, tasks, env_seed42):
        t = tasks[0]
        assert t["check"]("999999", env_seed42) is False

    def test_csv02_check_column_names(self, tasks, env_seed42):
        t = tasks[1]  # csv-02: column names
        assert t["check"]("order_id customer amount currency status timestamp", env_seed42)

    def test_csv03_check_completed_count(self, tasks, env_seed42):
        t = tasks[2]  # csv-03: completed count
        n = env_seed42.ground_truth["completed_order_count"]
        assert t["check"](str(n), env_seed42) is True


class TestValidationTasks:
    @pytest.fixture(scope="class")
    def tasks(self, env_seed42):
        return make_datacorp_validation_tasks(env_seed42)

    def test_returns_list(self, tasks):
        assert isinstance(tasks, list)

    def test_correct_count(self, tasks):
        assert len(tasks) == 10

    def test_task_ids(self, tasks):
        ids = [t["id"] for t in tasks]
        assert ids == [f"val-{i:02d}" for i in range(1, 11)]

    def test_all_phase_2(self, tasks):
        assert all(t["phase"] == 2 for t in tasks)

    def test_check_is_callable(self, tasks):
        for t in tasks:
            assert callable(t["check"])

    def test_val01_check_schema_names(self, tasks, env_seed42):
        t = tasks[0]  # val-01: list schemas
        assert t["check"]("orders products customers", env_seed42) is True

    def test_val04_check_dc001(self, tasks, env_seed42):
        t = tasks[3]  # val-04: error code for missing field
        assert t["check"]("DC-001 missing required field", env_seed42) is True

    def test_val07_check_dc008(self, tasks, env_seed42):
        t = tasks[6]  # val-07: duplicate key DC-008
        assert t["check"]("DC-008 order_id 2001 duplicated", env_seed42) is True

    def test_val10_check_dc007(self, tasks, env_seed42):
        t = tasks[9]  # val-10: cross-field DC-007
        assert t["check"]("DC-007 5002 cross-field constraint", env_seed42) is True


class TestQueryTasks:
    @pytest.fixture(scope="class")
    def tasks(self, env_seed42):
        return make_datacorp_query_tasks(env_seed42)

    def test_returns_list(self, tasks):
        assert isinstance(tasks, list)

    def test_correct_count(self, tasks):
        assert len(tasks) == 10

    def test_task_ids(self, tasks):
        ids = [t["id"] for t in tasks]
        assert ids == [f"qry-{i:02d}" for i in range(1, 11)]

    def test_all_phase_3(self, tasks):
        assert all(t["phase"] == 3 for t in tasks)

    def test_check_is_callable(self, tasks):
        for t in tasks:
            assert callable(t["check"])

    def test_qry01_check_with_correct_count(self, tasks, env_seed42):
        t = tasks[0]  # qry-01: completed orders count
        gt = env_seed42.ground_truth
        # completed count from CSV matches query result
        n = gt["completed_order_count"]
        assert t["check"](str(n), env_seed42) is True


class TestMakeDatacorpTasks:
    @pytest.fixture(scope="class")
    def all_tasks(self, env_seed42):
        return make_datacorp_tasks(env_seed42)

    def test_total_count_is_30(self, all_tasks):
        assert len(all_tasks) == 30

    def test_no_duplicate_ids(self, all_tasks):
        ids = [t["id"] for t in all_tasks]
        assert len(ids) == len(set(ids))

    def test_three_phases(self, all_tasks):
        phases = {t["phase"] for t in all_tasks}
        assert phases == {1, 2, 3}

    def test_10_tasks_per_phase(self, all_tasks):
        from collections import Counter
        counts = Counter(t["phase"] for t in all_tasks)
        assert counts[1] == 10
        assert counts[2] == 10
        assert counts[3] == 10

    def test_all_have_difficulty(self, all_tasks):
        for t in all_tasks:
            assert t["difficulty"] in ("easy", "medium", "hard")

    def test_all_have_check(self, all_tasks):
        for t in all_tasks:
            assert callable(t["check"])

    def test_all_have_task_string(self, all_tasks):
        for t in all_tasks:
            assert isinstance(t["task"], str)
            assert len(t["task"]) > 0
