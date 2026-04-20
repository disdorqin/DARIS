"""DataCorp fixture generator — seeded environment combining CSV data and validation API."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field

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
from benchmarks.datacorp.validation_api import SCHEMAS, validate_batch


@dataclass
class DataCorpEnv:
    csv_data: dict[str, str]          # filename -> CSV text
    csv_file_paths: dict[str, str]    # filename -> temp file path
    csv_parsed: dict[str, dict]       # filename -> parsed CSV dict
    schemas: dict                      # schema definitions
    validation_port: int
    ground_truth: dict
    _tmpdir: str = ""

    def cleanup(self):
        """Remove temp files."""
        if self._tmpdir and os.path.exists(self._tmpdir):
            import shutil
            shutil.rmtree(self._tmpdir)


def generate(
    seed: int = 42,
    order_count: int = 50,
    validation_port: int = 19080,
) -> DataCorpEnv:
    """Generate a complete DataCorp environment. Same seed = same data."""

    # 1. Generate CSV data
    orders_csv = generate_orders_csv(seed, count=order_count)
    products_csv = generate_products_csv(seed)
    customers_csv = generate_customers_csv(seed)

    csv_data = {
        "orders.dc": orders_csv,
        "products.dc": products_csv,
        "customers.dc": customers_csv,
    }

    # 2. Parse each CSV
    csv_parsed: dict[str, dict] = {}
    for filename, text in csv_data.items():
        csv_parsed[filename] = parse_datacorp_csv(text)

    # 3. Write CSV files to temp directory
    tmpdir = tempfile.mkdtemp(prefix="datacorp_")
    csv_file_paths: dict[str, str] = {}
    for filename, text in csv_data.items():
        path = os.path.join(tmpdir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        csv_file_paths[filename] = path

    # 4. Build ground_truth
    orders_parsed = csv_parsed["orders.dc"]
    products_parsed = csv_parsed["products.dc"]
    customers_parsed = csv_parsed["customers.dc"]

    orders_rows = orders_parsed["rows"]
    products_rows = products_parsed["rows"]
    customers_rows = customers_parsed["rows"]

    # CSV ground truth
    order_count_gt = gt_row_count(orders_parsed)
    product_count_gt = gt_row_count(products_parsed)
    customer_count_gt = gt_row_count(customers_parsed)

    completed_orders = gt_filter_rows(orders_parsed, "status", "completed")
    pending_orders = gt_filter_rows(orders_parsed, "status", "pending")
    failed_orders = gt_filter_rows(orders_parsed, "status", "failed")

    sum_by_currency = gt_sum_by_group(orders_parsed, "amount", "currency")
    sum_by_status = gt_sum_by_group(orders_parsed, "amount", "status")

    # All order amounts
    amounts = [row["amount"] for row in orders_rows if isinstance(row.get("amount"), (int, float))]
    total_amount = round(sum(amounts), 2)
    avg_amount = round(total_amount / len(amounts), 4) if amounts else 0.0

    # Pivot table: currency x status -> count
    pivot = gt_pivot_status_by_currency(orders_parsed)

    # Running average of amounts
    running_avg = gt_running_average(orders_parsed, "amount")

    # Duplicates (by customer — some customers have multiple orders)
    dup_customers = gt_detect_duplicates(orders_parsed, "customer")

    # USD orders
    usd_orders = gt_filter_rows(orders_parsed, "currency", "USD")
    usd_completed = [r for r in usd_orders if r.get("status") == "completed"]

    # Customers in product join (orders joined with customers on customer==email)
    customers_by_email = {row["email"]: row for row in customers_rows}
    orders_with_tier = []
    for row in orders_rows:
        email = row.get("customer", "")
        if email in customers_by_email:
            merged = {**row, "tier": customers_by_email[email].get("tier")}
            orders_with_tier.append(merged)

    # Validation ground truth — validate orders rows
    validation_result = validate_batch(
        [dict(r) for r in orders_rows],
        "orders",
    )

    ground_truth = {
        # CSV counts
        "order_count": order_count_gt,
        "product_count": product_count_gt,
        "customer_count": customer_count_gt,
        # Status filters
        "completed_order_count": len(completed_orders),
        "pending_order_count": len(pending_orders),
        "failed_order_count": len(failed_orders),
        # Aggregations
        "sum_by_currency": sum_by_currency,
        "sum_by_status": sum_by_status,
        "total_amount": total_amount,
        "avg_amount": avg_amount,
        # Pivot
        "pivot_status_by_currency": pivot,
        # Running average (last value = overall average)
        "running_avg_amounts": running_avg,
        "final_running_avg": running_avg[-1] if running_avg else 0.0,
        # Duplicates
        "duplicate_customers": sorted(dup_customers),
        "duplicate_customer_count": len(dup_customers),
        # Filtered
        "usd_order_count": len(usd_orders),
        "usd_completed_count": len(usd_completed),
        "orders_with_customer_tier_count": len(orders_with_tier),
        # Validation
        "validation_valid_count": validation_result["valid_count"],
        "validation_invalid_count": validation_result["invalid_count"],
        "validation_error_summary": validation_result["error_summary"],
        # Schemas
        "schema_names": list(SCHEMAS.keys()),
    }

    return DataCorpEnv(
        csv_data=csv_data,
        csv_file_paths=csv_file_paths,
        csv_parsed=csv_parsed,
        schemas=SCHEMAS,
        validation_port=validation_port,
        ground_truth=ground_truth,
        _tmpdir=tmpdir,
    )
