"""DataCorp mock validation API server.

Endpoints:
    POST /validate  — validate records against a schema
                      body: {"records": [...], "schema": "orders"}
                      returns: {"valid": [...], "invalid": [...], "errors": [...]}

    GET /schemas    — list available schemas

    GET /schemas/{name} — get schema definition with field types and constraints

Error codes:
    DC-001  missing required field
    DC-002  invalid field type
    DC-003  value out of range
    DC-004  invalid enum value
    DC-005  field length exceeded
    DC-006  invalid timestamp format
    DC-007  cross-field constraint violation
    DC-008  duplicate primary key
    DC-009  reference integrity violation
    DC-010  schema not found
"""

from __future__ import annotations

import threading
import time
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Schema definitions
# ---------------------------------------------------------------------------

SCHEMAS: dict[str, dict] = {
    "orders": {
        "name": "orders",
        "description": "Customer order records",
        "fields": {
            "order_id": {"type": "integer", "required": True, "min": 1},
            "customer": {"type": "email", "required": True, "max_length": 100},
            "amount": {"type": "float", "required": True, "min": 0.01, "max": 999999.99},
            "currency": {"type": "enum", "required": True, "values": ["USD", "EUR", "GBP", "JPY", "CAD", "AUD"]},
            "status": {"type": "enum", "required": True, "values": ["completed", "pending", "failed", "refunded", "processing"]},
            "timestamp": {"type": "unix_timestamp", "required": True, "min": 0},
        },
        "constraints": [
            {"type": "cross_field", "rule": "if status == 'refunded' then amount > 0", "code": "DC-007"},
        ],
        "primary_key": "order_id",
    },
    "products": {
        "name": "products",
        "description": "Product catalog records",
        "fields": {
            "product_id": {"type": "integer", "required": True, "min": 1},
            "name": {"type": "string", "required": True, "max_length": 50},
            "price": {"type": "float", "required": True, "min": 0.01},
            "currency": {"type": "enum", "required": True, "values": ["USD", "EUR", "GBP"]},
            "category": {"type": "enum", "required": True, "values": ["hardware", "software", "service", "bundle"]},
            "in_stock": {"type": "boolean", "required": True},
        },
        "constraints": [],
        "primary_key": "product_id",
    },
    "customers": {
        "name": "customers",
        "description": "Customer account records",
        "fields": {
            "customer_id": {"type": "integer", "required": True, "min": 1},
            "email": {"type": "email", "required": True, "max_length": 100},
            "name": {"type": "string", "required": True, "max_length": 100},
            "country": {"type": "enum", "required": True, "values": ["US", "DE", "GB", "FR", "CA", "AU", "JP"]},
            "tier": {"type": "enum", "required": True, "values": ["free", "basic", "premium", "enterprise"]},
            "joined_ts": {"type": "unix_timestamp", "required": True, "min": 0},
        },
        "constraints": [],
        "primary_key": "customer_id",
    },
}


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------

def _is_valid_email(val: str) -> bool:
    return isinstance(val, str) and "@" in val and "." in val.split("@", 1)[1]


def validate_record(record: dict, schema_def: dict) -> list[dict]:
    """Validate a single record against a schema definition.

    Returns list of error dicts (empty list = valid).
    Each error: {"field": str, "code": str, "message": str}
    """
    errors: list[dict] = []
    fields = schema_def["fields"]

    # Check required fields and type/range
    for field_name, field_def in fields.items():
        val = record.get(field_name)

        # DC-001: missing required
        if field_def.get("required") and (val is None or val == ""):
            errors.append({
                "field": field_name,
                "code": "DC-001",
                "message": f"Missing required field '{field_name}'",
            })
            continue

        if val is None:
            continue

        ftype = field_def["type"]

        # DC-002: type validation
        if ftype == "integer":
            if not isinstance(val, int) or isinstance(val, bool):
                # Allow string ints
                try:
                    val = int(val)
                    record[field_name] = val
                except (ValueError, TypeError):
                    errors.append({"field": field_name, "code": "DC-002",
                                   "message": f"Field '{field_name}' must be integer, got {type(val).__name__}"})
                    continue

        elif ftype == "float":
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                try:
                    val = float(val)
                    record[field_name] = val
                except (ValueError, TypeError):
                    errors.append({"field": field_name, "code": "DC-002",
                                   "message": f"Field '{field_name}' must be float, got {type(val).__name__}"})
                    continue

        elif ftype == "email":
            if not _is_valid_email(str(val)):
                errors.append({"field": field_name, "code": "DC-002",
                               "message": f"Field '{field_name}' must be valid email"})
                continue

        elif ftype == "boolean":
            if isinstance(val, str):
                if val.lower() in ("true", "false"):
                    record[field_name] = val.lower() == "true"
                    val = record[field_name]
                else:
                    errors.append({"field": field_name, "code": "DC-002",
                                   "message": f"Field '{field_name}' must be boolean (true/false)"})
                    continue
            elif not isinstance(val, bool):
                errors.append({"field": field_name, "code": "DC-002",
                               "message": f"Field '{field_name}' must be boolean"})
                continue

        elif ftype == "unix_timestamp":
            if not isinstance(val, int) or isinstance(val, bool):
                try:
                    val = int(val)
                    record[field_name] = val
                except (ValueError, TypeError):
                    errors.append({"field": field_name, "code": "DC-006",
                                   "message": f"Field '{field_name}' must be unix timestamp (integer)"})
                    continue

        # DC-003: range validation
        if "min" in field_def and isinstance(val, (int, float)):
            if val < field_def["min"]:
                errors.append({"field": field_name, "code": "DC-003",
                               "message": f"Field '{field_name}' value {val} below minimum {field_def['min']}"})

        if "max" in field_def and isinstance(val, (int, float)):
            if val > field_def["max"]:
                errors.append({"field": field_name, "code": "DC-003",
                               "message": f"Field '{field_name}' value {val} exceeds maximum {field_def['max']}"})

        # DC-004: enum validation
        if ftype == "enum" and "values" in field_def:
            if str(val) not in field_def["values"]:
                errors.append({"field": field_name, "code": "DC-004",
                               "message": f"Field '{field_name}' value '{val}' not in allowed values: {field_def['values']}"})

        # DC-005: length validation
        if "max_length" in field_def and isinstance(val, str):
            if len(val) > field_def["max_length"]:
                errors.append({"field": field_name, "code": "DC-005",
                               "message": f"Field '{field_name}' length {len(val)} exceeds max {field_def['max_length']}"})

    # DC-007: cross-field constraints
    # (simplified: for orders, a refunded order with amount <= 0 is invalid)
    if schema_def.get("name") == "orders":
        status = record.get("status")
        amount = record.get("amount")
        if status == "refunded" and isinstance(amount, (int, float)) and amount <= 0:
            errors.append({"field": "amount", "code": "DC-007",
                           "message": "Refunded orders must have amount > 0"})

    return errors


def validate_batch(
    records: list[dict],
    schema_name: str,
) -> dict:
    """Validate a batch of records against the named schema.

    Returns:
        {
            "schema": str,
            "total": int,
            "valid_count": int,
            "invalid_count": int,
            "valid": [{"index": int, "record": dict}],
            "invalid": [{"index": int, "record": dict, "errors": [...]}],
            "error_summary": {"DC-001": int, ...},
        }
    """
    if schema_name not in SCHEMAS:
        return {
            "schema": schema_name,
            "error": f"Schema '{schema_name}' not found",
            "code": "DC-010",
        }

    schema_def = SCHEMAS[schema_name]
    valid = []
    invalid = []
    error_summary: dict[str, int] = {}

    # Track primary keys for DC-008
    seen_pks: set = set()
    pk_field = schema_def.get("primary_key", "")

    for idx, record in enumerate(records):
        rec_copy = dict(record)

        # DC-008: duplicate primary key check
        pk_errors = []
        if pk_field and pk_field in rec_copy:
            pk_val = rec_copy[pk_field]
            if pk_val in seen_pks:
                pk_errors.append({
                    "field": pk_field,
                    "code": "DC-008",
                    "message": f"Duplicate primary key value '{pk_val}' for field '{pk_field}'",
                })
            else:
                seen_pks.add(pk_val)

        field_errors = validate_record(rec_copy, schema_def)
        all_errors = pk_errors + field_errors

        if all_errors:
            invalid.append({"index": idx, "record": rec_copy, "errors": all_errors})
            for err in all_errors:
                code = err["code"]
                error_summary[code] = error_summary.get(code, 0) + 1
        else:
            valid.append({"index": idx, "record": rec_copy})

    return {
        "schema": schema_name,
        "total": len(records),
        "valid_count": len(valid),
        "invalid_count": len(invalid),
        "valid": valid,
        "invalid": invalid,
        "error_summary": error_summary,
    }


def auto_fix_record(record: dict, schema_name: str) -> tuple[dict, list[str]]:
    """Attempt to auto-fix a record's validation errors.

    Returns (fixed_record, list_of_fixes_applied).
    """
    if schema_name not in SCHEMAS:
        return record, []

    schema_def = SCHEMAS[schema_name]
    fixed = dict(record)
    fixes: list[str] = []

    fields = schema_def["fields"]

    for field_name, field_def in fields.items():
        val = fixed.get(field_name)
        ftype = field_def["type"]

        # Fix type mismatches
        if ftype in ("integer", "unix_timestamp") and val is not None:
            try:
                int_val = int(val)
                if int_val != val:
                    fixed[field_name] = int_val
                    fixes.append(f"Converted '{field_name}' to integer: {int_val}")
            except (ValueError, TypeError):
                pass

        elif ftype == "float" and val is not None:
            try:
                float_val = float(val)
                if float_val != val:
                    fixed[field_name] = float_val
                    fixes.append(f"Converted '{field_name}' to float: {float_val}")
            except (ValueError, TypeError):
                pass

        elif ftype == "boolean" and isinstance(val, str):
            if val.lower() in ("true", "1", "yes"):
                fixed[field_name] = True
                fixes.append(f"Converted '{field_name}' to boolean True")
            elif val.lower() in ("false", "0", "no"):
                fixed[field_name] = False
                fixes.append(f"Converted '{field_name}' to boolean False")

        # Fix range violations by clamping
        if "min" in field_def and isinstance(fixed.get(field_name), (int, float)):
            if fixed[field_name] < field_def["min"]:
                fixed[field_name] = field_def["min"]
                fixes.append(f"Clamped '{field_name}' to minimum {field_def['min']}")

        if "max" in field_def and isinstance(fixed.get(field_name), (int, float)):
            if fixed[field_name] > field_def["max"]:
                fixed[field_name] = field_def["max"]
                fixes.append(f"Clamped '{field_name}' to maximum {field_def['max']}")

        # Fix enum by using first allowed value as default
        if ftype == "enum" and "values" in field_def:
            if str(fixed.get(field_name, "")) not in field_def["values"]:
                default = field_def["values"][0]
                fixed[field_name] = default
                fixes.append(f"Set '{field_name}' to default enum value '{default}'")

    return fixed, fixes


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

class ValidateRequest(BaseModel):
    records: list[dict]
    schema: str


def create_validation_app() -> FastAPI:
    """Create a FastAPI app exposing the DataCorp Validation API."""
    app = FastAPI(title="DataCorp Validation API")

    @app.get("/schemas")
    def list_schemas() -> list[str]:
        """List all available schema names."""
        return list(SCHEMAS.keys())

    @app.get("/schemas/{name}")
    def get_schema(name: str) -> dict:
        """Get schema definition by name."""
        if name not in SCHEMAS:
            raise HTTPException(status_code=404, detail=f"Schema '{name}' not found (DC-010)")
        return SCHEMAS[name]

    @app.post("/validate")
    def validate(req: ValidateRequest) -> dict:
        """Validate records against a schema.

        Body: {"records": [...], "schema": "orders"}
        Returns validation results with DC-xxx error codes.
        """
        result = validate_batch(req.records, req.schema)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result

    return app


# ---------------------------------------------------------------------------
# Server lifecycle helpers
# ---------------------------------------------------------------------------

class _UvicornServer(uvicorn.Server):
    """Uvicorn server that can be stopped programmatically."""

    def install_signal_handlers(self) -> None:  # type: ignore[override]
        pass


def start_validation_server(port: int = 19080) -> threading.Thread:
    """Start the validation server in a daemon thread.

    Returns:
        The daemon thread running the server.
    """
    app = create_validation_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = _UvicornServer(config=config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait briefly until the server is ready
    deadline = time.time() + 5.0
    while not server.started and time.time() < deadline:
        time.sleep(0.05)

    thread._dc_server = server  # type: ignore[attr-defined]
    return thread


def stop_validation_server(thread: threading.Thread) -> None:
    """Signal the validation server to shut down."""
    server: _UvicornServer = getattr(thread, "_dc_server", None)
    if server is not None:
        server.should_exit = True
    thread.join(timeout=5.0)
