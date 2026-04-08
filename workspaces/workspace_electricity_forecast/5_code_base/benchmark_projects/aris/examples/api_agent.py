"""
ARISE Real-World Test — HTTP/API Agent

A mock REST API server runs locally. The agent starts with ONLY http_get and
http_post — no JSON parsing, no auth handling, no pagination. It must evolve
those capabilities through tool creation.

The mock API has:
- /auth/token      — POST with credentials to get a Bearer token
- /users           — GET (paginated, requires auth)
- /users/:id       — GET (requires auth)
- /products        — GET (paginated, filterable by ?category=)
- /orders          — POST (requires auth + JSON body)
- /analytics/summary — GET (requires auth, returns nested JSON)
- Rate limiting: 429 after 5 rapid requests

Usage:
    export OPENAI_API_KEY=sk-...
    python examples/api_agent.py
"""

import os
import sys
import json
import shutil
import inspect
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arise import ARISE, Sandbox, SkillLibrary, ToolSpec
from arise.config import ARISEConfig
from arise.types import Skill, SkillOrigin, SkillStatus, Trajectory


# =============================================================================
# Mock API Server
# =============================================================================

VALID_TOKEN = "arise-test-token-42"
VALID_CREDENTIALS = {"username": "admin", "password": "secret123"}

USERS_DB = [
    {"id": 1, "name": "Alice Chen", "email": "alice@example.com", "role": "engineer", "department": "backend"},
    {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "role": "designer", "department": "frontend"},
    {"id": 3, "name": "Carol Wu", "email": "carol@example.com", "role": "manager", "department": "backend"},
    {"id": 4, "name": "Dave Jones", "email": "dave@example.com", "role": "engineer", "department": "data"},
    {"id": 5, "name": "Eve Brown", "email": "eve@example.com", "role": "engineer", "department": "frontend"},
    {"id": 6, "name": "Frank Lee", "email": "frank@example.com", "role": "designer", "department": "mobile"},
    {"id": 7, "name": "Grace Kim", "email": "grace@example.com", "role": "manager", "department": "data"},
    {"id": 8, "name": "Henry Patel", "email": "henry@example.com", "role": "engineer", "department": "backend"},
]

PRODUCTS_DB = [
    {"id": 101, "name": "Widget A", "category": "hardware", "price": 29.99, "stock": 150},
    {"id": 102, "name": "Widget B", "category": "hardware", "price": 49.99, "stock": 0},
    {"id": 103, "name": "SDK Pro", "category": "software", "price": 99.00, "stock": 999},
    {"id": 104, "name": "Cable X", "category": "hardware", "price": 12.50, "stock": 300},
    {"id": 105, "name": "Cloud Suite", "category": "software", "price": 199.00, "stock": 999},
    {"id": 106, "name": "Dongle Z", "category": "hardware", "price": 15.00, "stock": 45},
]

ORDERS_DB = []

_request_timestamps = []


class MockAPIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress request logging

    def _check_rate_limit(self):
        now = time.time()
        _request_timestamps.append(now)
        recent = [t for t in _request_timestamps if now - t < 2]
        _request_timestamps.clear()
        _request_timestamps.extend(recent)
        if len(recent) > 5:
            self._json_response(429, {"error": "Rate limited. Max 5 requests per 2 seconds.", "retry_after_seconds": 2})
            return False
        return True

    def _check_auth(self):
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or auth[7:] != VALID_TOKEN:
            self._json_response(401, {"error": "Unauthorized. Get a token via POST /auth/token"})
            return False
        return True

    def _json_response(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def _paginate(self, items, params):
        page = int(params.get("page", ["1"])[0])
        per_page = int(params.get("per_page", ["3"])[0])
        start = (page - 1) * per_page
        end = start + per_page
        total_pages = (len(items) + per_page - 1) // per_page
        return {
            "data": items[start:end],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_items": len(items),
                "total_pages": total_pages,
                "has_next": page < total_pages,
            }
        }

    def do_GET(self):
        if not self._check_rate_limit():
            return

        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/users":
            if not self._check_auth():
                return
            self._json_response(200, self._paginate(USERS_DB, params))

        elif path.startswith("/users/"):
            if not self._check_auth():
                return
            try:
                uid = int(path.split("/")[-1])
                user = next((u for u in USERS_DB if u["id"] == uid), None)
                if user:
                    self._json_response(200, user)
                else:
                    self._json_response(404, {"error": f"User {uid} not found"})
            except ValueError:
                self._json_response(400, {"error": "Invalid user ID"})

        elif path == "/products":
            items = PRODUCTS_DB
            category = params.get("category", [None])[0]
            if category:
                items = [p for p in items if p["category"] == category]
            in_stock = params.get("in_stock", [None])[0]
            if in_stock == "true":
                items = [p for p in items if p["stock"] > 0]
            self._json_response(200, self._paginate(items, params))

        elif path == "/analytics/summary":
            if not self._check_auth():
                return
            summary = {
                "users": {
                    "total": len(USERS_DB),
                    "by_department": {},
                    "by_role": {},
                },
                "products": {
                    "total": len(PRODUCTS_DB),
                    "out_of_stock": len([p for p in PRODUCTS_DB if p["stock"] == 0]),
                    "total_value": sum(p["price"] * p["stock"] for p in PRODUCTS_DB),
                    "by_category": {},
                },
                "orders": {
                    "total": len(ORDERS_DB),
                    "total_revenue": sum(o.get("total", 0) for o in ORDERS_DB),
                },
            }
            for u in USERS_DB:
                dept = u["department"]
                role = u["role"]
                summary["users"]["by_department"][dept] = summary["users"]["by_department"].get(dept, 0) + 1
                summary["users"]["by_role"][role] = summary["users"]["by_role"].get(role, 0) + 1
            for p in PRODUCTS_DB:
                cat = p["category"]
                summary["products"]["by_category"][cat] = summary["products"]["by_category"].get(cat, 0) + 1
            self._json_response(200, summary)

        else:
            self._json_response(404, {"error": f"Unknown endpoint: {path}"})

    def do_POST(self):
        if not self._check_rate_limit():
            return

        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else "{}"
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._json_response(400, {"error": "Invalid JSON body"})
            return

        if path == "/auth/token":
            if data.get("username") == VALID_CREDENTIALS["username"] and data.get("password") == VALID_CREDENTIALS["password"]:
                self._json_response(200, {"token": VALID_TOKEN, "expires_in": 3600})
            else:
                self._json_response(401, {"error": "Invalid credentials"})

        elif path == "/orders":
            if not self._check_auth():
                return
            required = ["product_id", "quantity"]
            missing = [f for f in required if f not in data]
            if missing:
                self._json_response(400, {"error": f"Missing fields: {missing}"})
                return
            product = next((p for p in PRODUCTS_DB if p["id"] == data["product_id"]), None)
            if not product:
                self._json_response(404, {"error": f"Product {data['product_id']} not found"})
                return
            if product["stock"] < data["quantity"]:
                self._json_response(409, {"error": f"Insufficient stock. Available: {product['stock']}"})
                return
            order = {
                "id": len(ORDERS_DB) + 1,
                "product_id": data["product_id"],
                "product_name": product["name"],
                "quantity": data["quantity"],
                "total": product["price"] * data["quantity"],
                "status": "confirmed",
            }
            ORDERS_DB.append(order)
            product["stock"] -= data["quantity"]
            self._json_response(201, order)

        else:
            self._json_response(404, {"error": f"Unknown endpoint: {path}"})


def start_mock_server(port=18932):
    server = HTTPServer(("127.0.0.1", port), MockAPIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


# =============================================================================
# Agent Tools — intentionally minimal
# =============================================================================

def http_get(url: str) -> str:
    """Send an HTTP GET request to a URL. Returns the response body as a string."""
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode()
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return f"HTTP {e.code}: {body}"
    except Exception as e:
        return f"Error: {e}"


def http_post(url: str, body: str) -> str:
    """Send an HTTP POST request with a JSON body string. Returns response body."""
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(
            url,
            data=body.encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode()
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode() if e.fp else ""
        return f"HTTP {e.code}: {resp_body}"
    except Exception as e:
        return f"Error: {e}"


# =============================================================================
# Reward
# =============================================================================

def api_reward(trajectory: Trajectory) -> float:
    outcome = trajectory.outcome
    if not outcome:
        return 0.0

    # Hard failures
    if outcome.startswith("Error:"):
        return 0.0
    if "TOOL_MISSING" in outcome:
        return 0.1

    # Got an HTTP error in the final result
    if "HTTP 401" in outcome or "HTTP 429" in outcome:
        return 0.1
    if "HTTP 4" in outcome or "HTTP 5" in outcome:
        return 0.2

    # Check tool usage
    tool_calls = [s for s in trajectory.steps if s.action not in ("respond", "error")]
    errors = [s for s in trajectory.steps if s.error]

    if errors:
        return 0.3
    if not tool_calls:
        return 0.2  # Didn't use tools
    return 1.0


# =============================================================================
# Agent
# =============================================================================

def api_agent(task: str, tools: list[ToolSpec]) -> str:
    from arise.llm import llm_call

    tool_descs = []
    tool_map = {}
    for t in tools:
        params = ", ".join(f"{k}: {v.get('type', 'any')}" for k, v in t.parameters.get("properties", {}).items())
        tool_descs.append(f"- {t.name}({params}): {t.description}")
        tool_map[t.name] = t.fn

    prompt = f"""\
You are an API integration agent. You interact with REST APIs using the provided tools.

AVAILABLE TOOLS:
{chr(10).join(tool_descs)}

TASK: {task}

RULES:
- You MUST use ONLY the provided tool functions. No urllib, requests, or other HTTP libraries directly.
- Parse JSON responses using json.loads() from the standard library.
- If you get HTTP 401, you need to authenticate first.
- If you get HTTP 429, you're rate limited — wait and retry.
- If an API returns paginated results, you may need to fetch multiple pages.
- If no tool can do what you need, print("TOOL_MISSING: <describe what you need>")
- Print the final answer clearly.

Write Python code. Return ONLY code, no markdown."""

    code = llm_call([{"role": "user", "content": prompt}], model="gpt-4o-mini")
    code = code.strip()
    if code.startswith("```"):
        lines = code.split("\n")
        code = "\n".join(l for l in lines[1:] if l.strip() != "```")

    namespace = {**tool_map, "json": __import__("json"), "time": __import__("time")}
    import io, contextlib
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, namespace)  # noqa: S102
        output = buf.getvalue().strip()
        return output if output else "No output"
    except Exception as e:
        return f"Error: {e}"


# =============================================================================
# Main
# =============================================================================

def main():
    for d in ["./arise_skills_api", "./arise_trajectories_api"]:
        if os.path.exists(d):
            shutil.rmtree(d)

    PORT = 18932
    BASE = f"http://127.0.0.1:{PORT}"
    server = start_mock_server(PORT)
    print(f"Mock API server running on {BASE}")

    # Verify server is up
    time.sleep(0.5)
    import urllib.request
    try:
        with urllib.request.urlopen(f"{BASE}/products?per_page=1", timeout=2) as r:
            pass
    except Exception as e:
        print(f"Server failed to start: {e}")
        return

    library = SkillLibrary("./arise_skills_api")

    for fn, desc in [
        (http_get, "Send HTTP GET request, returns response body string"),
        (http_post, "Send HTTP POST with JSON body string, returns response body"),
    ]:
        skill = Skill(
            name=fn.__name__,
            description=desc,
            implementation=inspect.getsource(fn),
            origin=SkillOrigin.MANUAL,
            status=SkillStatus.ACTIVE,
        )
        library.add(skill)
        library.promote(skill.id)

    agent = ARISE(
        agent_fn=api_agent,
        reward_fn=api_reward,
        model="gpt-4o-mini",
        sandbox=Sandbox(backend="subprocess"),
        skill_library=library,
        config=ARISEConfig(
            model="gpt-4o-mini",
            skill_store_path="./arise_skills_api",
            trajectory_store_path="./arise_trajectories_api",
            failure_threshold=3,
            max_evolutions_per_hour=10,
            verbose=True,
        ),
    )

    tasks = [
        # Phase 1: Simple — should work with just http_get
        f"List all products from {BASE}/products (fetch ALL pages, the API paginates with 3 items per page)",

        # Phase 2: Auth required — agent has http_post but no auth tool
        f"Get an auth token from {BASE}/auth/token by POSTing {{\"username\": \"admin\", \"password\": \"secret123\"}}. Then use the token to fetch all users from {BASE}/users (paginated). List all user names and their departments.",

        # Phase 3: Filtering and analysis
        f"Fetch all hardware products from {BASE}/products?category=hardware and calculate the total inventory value (price * stock for each). Report the total.",

        # Phase 4: Auth + complex operation
        f"Authenticate at {BASE}/auth/token (username: admin, password: secret123), then fetch {BASE}/analytics/summary. Report: total users, users per department, out-of-stock products count, total product inventory value.",

        # Phase 5: Write operation — place an order
        f"Authenticate at {BASE}/auth/token (username: admin, password: secret123). Then place an order via POST {BASE}/orders with Bearer auth. Order 3 units of product_id 101. Report the order confirmation.",

        # Phase 6: Multi-step workflow
        f"Authenticate at {BASE}/auth/token (username: admin, password: secret123). Fetch all users from {BASE}/users (all pages). Count how many engineers are in each department. Then fetch all in-stock software products from {BASE}/products?category=software&in_stock=true. Report both results.",

        # Phase 7: Re-run earlier hard tasks to see improvement
        f"Get a token from {BASE}/auth/token (username: admin, password: secret123). Use it to GET {BASE}/analytics/summary. Extract and report: (1) which department has the most users, (2) total product inventory value, (3) number of orders placed.",

        # Phase 8: Error handling
        f"Try to place an order at {BASE}/orders for product_id 102, quantity 5 (authenticate first at {BASE}/auth/token with username admin, password secret123). This product is out of stock — handle the error gracefully and report what happened.",
    ]

    print("=" * 70)
    print("ARISE Real-World Test — HTTP/API Agent")
    print("=" * 70)

    for i, task in enumerate(tasks):
        print(f"\n{'=' * 70}")
        print(f"Task {i + 1}/{len(tasks)}")
        # Show a shorter version of the task
        short = task.replace(BASE, "<API>")
        if len(short) > 100:
            short = short[:97] + "..."
        print(f"  {short}")
        print("-" * 70)
        result = agent.run(task)
        if len(result) > 600:
            print(f"Result:\n{result[:600]}\n... ({len(result)} chars)")
        else:
            print(f"Result:\n{result}")

    # Summary
    print(f"\n{'=' * 70}")
    print("FINAL REPORT")
    print("=" * 70)
    stats = agent.stats
    print(f"Episodes:             {stats['episodes_run']}")
    print(f"Active skills:        {stats['active']}")
    print(f"Total skills created: {stats['total_skills']}")
    print(f"Success rate:         {stats['recent_success_rate']:.0%}")

    print("\nActive Skills:")
    for skill in agent.skills:
        origin = skill.origin.value
        rate = f"{skill.success_rate:.0%}" if skill.invocation_count > 0 else "n/a"
        print(f"  [{origin:>11}] {skill.name:<35} success={rate}, calls={skill.invocation_count}")

    synthesized = [s for s in agent.skills if s.origin in (SkillOrigin.SYNTHESIZED, SkillOrigin.REFINED)]
    if synthesized:
        print(f"\nTools the agent created:")
        for s in synthesized:
            print(f"\n  --- {s.name} ---")
            print(f"  {s.description}")
            lines = s.implementation.strip().split("\n")
            preview = "\n".join(f"    {l}" for l in lines[:10])
            if len(lines) > 10:
                preview += f"\n    ... ({len(lines)} lines)"
            print(preview)

    server.shutdown()
    shutil.rmtree("./arise_skills_api", ignore_errors=True)
    shutil.rmtree("./arise_trajectories_api", ignore_errors=True)


if __name__ == "__main__":
    main()
