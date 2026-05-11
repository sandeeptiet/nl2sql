"""
nl2sql Evaluation Harness
Runs 25 test queries through the live API and measures:
  - Execution Accuracy (EX): generated result set matches golden result set
  - Exact Match Rate  (EM):  generated SQL is structurally identical to golden SQL (sqlglot AST diff)

Usage:
    cd /path/to/nl2sql
    uv run python evaluation/eval.py                        # defaults: localhost:8000
    uv run python evaluation/eval.py --api http://host:8000
    uv run python evaluation/eval.py --report               # also write docs/eval_report.md
"""

import os
import sys
import json
import argparse
import requests
import pymysql
import sqlglot
import sqlglot.diff
from decimal import Decimal
from datetime import datetime, date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env.local"))

# ── CLI args ──────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--api", default="http://localhost:8000", help="Backend base URL")
parser.add_argument("--report", action="store_true", help="Write docs/eval_report.md")
parser.add_argument("--verbose", action="store_true", help="Print generated SQL for every query")
args = parser.parse_args()

API_URL = f"{args.api}/api/v1/query"

# ── 25 test cases ─────────────────────────────────────────────
TEST_CASES = [
    # ── SELECT_SIMPLE (6) ─────────────────────────────────────
    {
        "id": "S1",
        "question": "Which products are currently in stock?",
        "golden_sql": "SELECT id, name, price, stock FROM products WHERE stock > 0 AND is_active = 1 LIMIT 100",
        "query_type": "SELECT_SIMPLE",
    },
    {
        "id": "S2",
        "question": "Show all processing orders",
        "golden_sql": "SELECT id, customer_id, total, created_at FROM orders WHERE status = 'processing' LIMIT 100",
        "query_type": "SELECT_SIMPLE",
    },
    {
        "id": "S3",
        "question": "List all product categories",
        "golden_sql": "SELECT id, name FROM categories LIMIT 100",
        "query_type": "SELECT_SIMPLE",
    },
    {
        "id": "S4",
        "question": "Show products priced above 5000",
        "golden_sql": "SELECT id, name, price FROM products WHERE price > 5000 LIMIT 100",
        "query_type": "SELECT_SIMPLE",
    },
    {
        "id": "S5",
        "question": "List all 1-star reviews",
        "golden_sql": "SELECT id, product_id, customer_id, comment, created_at FROM reviews WHERE rating = 1 LIMIT 100",
        "query_type": "SELECT_SIMPLE",
    },
    {
        "id": "S6",
        "question": "Show all delivered orders",
        "golden_sql": "SELECT id, customer_id, total, delivered_at FROM orders WHERE status = 'delivered' LIMIT 100",
        "query_type": "SELECT_SIMPLE",
    },
    # ── SELECT_AGGREGATE (6) ──────────────────────────────────
    {
        "id": "A1",
        "question": "How many total customers are there?",
        "golden_sql": "SELECT COUNT(*) AS total_customers FROM customers",
        "query_type": "SELECT_AGGREGATE",
    },
    {
        "id": "A2",
        "question": "What is the total revenue?",
        "golden_sql": "SELECT SUM(total) AS total_revenue FROM orders WHERE status != 'cancelled'",
        "query_type": "SELECT_AGGREGATE",
    },
    {
        "id": "A3",
        "question": "What is the average order value?",
        "golden_sql": "SELECT AVG(total) AS avg_order_value FROM orders WHERE status != 'cancelled'",
        "query_type": "SELECT_AGGREGATE",
    },
    {
        "id": "A4",
        "question": "How many orders per status?",
        "golden_sql": "SELECT status, COUNT(*) AS order_count FROM orders GROUP BY status ORDER BY order_count DESC LIMIT 100",
        "query_type": "SELECT_AGGREGATE",
    },
    {
        "id": "A5",
        "question": "What is the average product rating?",
        "golden_sql": "SELECT AVG(rating) AS avg_rating FROM reviews",
        "query_type": "SELECT_AGGREGATE",
    },
    {
        "id": "A6",
        "question": "What is the most expensive product?",
        "golden_sql": "SELECT name, price FROM products ORDER BY price DESC LIMIT 1",
        "query_type": "SELECT_AGGREGATE",
    },
    # ── SELECT_JOIN (7) ───────────────────────────────────────
    {
        "id": "J1",
        "question": "Show all orders with customer details",
        "golden_sql": "SELECT o.id, c.name, c.email, o.status, o.total, o.created_at FROM orders o JOIN customers c ON o.customer_id = c.id ORDER BY o.created_at DESC LIMIT 100",
        "query_type": "SELECT_JOIN",
    },
    {
        "id": "J2",
        "question": "List all products with their category",
        "golden_sql": "SELECT p.name, c.name AS category, p.price FROM products p JOIN categories c ON p.category_id = c.id LIMIT 100",
        "query_type": "SELECT_JOIN",
    },
    {
        "id": "J3",
        "question": "Top 5 customers by total spending",
        "golden_sql": "SELECT c.name, c.email, SUM(o.total) AS total_spent FROM customers c JOIN orders o ON c.id = o.customer_id WHERE o.status != 'cancelled' GROUP BY c.id, c.name, c.email ORDER BY total_spent DESC LIMIT 5",
        "query_type": "SELECT_JOIN",
    },
    {
        "id": "J4",
        "question": "Find customers with no orders",
        "golden_sql": "SELECT c.id, c.name, c.email FROM customers c LEFT JOIN orders o ON c.id = o.customer_id WHERE o.id IS NULL LIMIT 100",
        "query_type": "SELECT_JOIN",
    },
    {
        "id": "J5",
        "question": "Top 5 products by units sold",
        "golden_sql": "SELECT p.name, SUM(oi.quantity) AS total_sold FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.id, p.name ORDER BY total_sold DESC LIMIT 5",
        "query_type": "SELECT_JOIN",
    },
    {
        "id": "J6",
        "question": "Revenue breakdown by product category",
        "golden_sql": "SELECT c.name AS category, SUM(oi.subtotal) AS revenue FROM order_items oi JOIN products p ON oi.product_id = p.id JOIN categories c ON p.category_id = c.id GROUP BY c.name ORDER BY revenue DESC LIMIT 100",
        "query_type": "SELECT_JOIN",
    },
    {
        "id": "J7",
        "question": "Show reviews with customer and product names",
        "golden_sql": "SELECT c.name AS customer, p.name AS product, r.rating, r.created_at FROM reviews r JOIN customers c ON r.customer_id = c.id JOIN products p ON r.product_id = p.id LIMIT 100",
        "query_type": "SELECT_JOIN",
    },
    # ── SELECT_TEMPORAL (6) ───────────────────────────────────
    {
        "id": "T1",
        "question": "What orders were placed in the last month?",
        "golden_sql": "SELECT id, status, total, created_at FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) ORDER BY created_at DESC LIMIT 100",
        "query_type": "SELECT_TEMPORAL",
    },
    {
        "id": "T2",
        "question": "Show monthly revenue for the past year",
        "golden_sql": "SELECT DATE_FORMAT(created_at, '%Y-%m') AS month, SUM(total) AS revenue FROM orders WHERE status != 'cancelled' AND created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH) GROUP BY month ORDER BY month LIMIT 100",
        "query_type": "SELECT_TEMPORAL",
    },
    {
        "id": "T3",
        "question": "How many new customers signed up this month?",
        "golden_sql": "SELECT COUNT(*) AS new_customers FROM customers WHERE YEAR(created_at) = YEAR(CURDATE()) AND MONTH(created_at) = MONTH(CURDATE())",
        "query_type": "SELECT_TEMPORAL",
    },
    {
        "id": "T4",
        "question": "Orders from the past week that were delivered",
        "golden_sql": "SELECT id, customer_id, total, delivered_at FROM orders WHERE status = 'delivered' AND delivered_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) LIMIT 100",
        "query_type": "SELECT_TEMPORAL",
    },
    {
        "id": "T5",
        "question": "How many orders were placed each month in 2024?",
        "golden_sql": "SELECT DATE_FORMAT(created_at, '%Y-%m') AS month, COUNT(*) AS order_count FROM orders WHERE YEAR(created_at) = 2024 GROUP BY month ORDER BY month LIMIT 100",
        "query_type": "SELECT_TEMPORAL",
    },
    {
        "id": "T6",
        "question": "Show customers who joined in the last 3 months",
        "golden_sql": "SELECT id, name, email, created_at FROM customers WHERE created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY) ORDER BY created_at DESC LIMIT 100",
        "query_type": "SELECT_TEMPORAL",
    },
]

# ── DB connection (read-only) ─────────────────────────────────
def get_conn():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_READONLY_USER", os.getenv("DB_USER", "")),
        password=os.getenv("DB_READONLY_PASSWORD", os.getenv("DB_PASSWORD", "")),
        database=os.getenv("DB_NAME", ""),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def normalize_value(v) -> str:
    """Normalize a single cell value to a string for comparison."""
    if v is None:
        return ""
    if isinstance(v, (float, Decimal)):
        # Round to 2dp — matches MySQL DECIMAL(10,2) and handles AVG/ROUND differences
        return f"{round(float(v), 2):.2f}"
    if isinstance(v, (datetime, date)):
        # pymysql returns datetime objects; truncate to seconds
        return str(v)[:19]
    s = str(v).strip()
    # FastAPI serializes datetimes as ISO 8601 with 'T'; pymysql uses space separator
    if len(s) >= 19 and s[4:5] == "-" and s[7:8] == "-" and s[10:11] == "T":
        s = s[:10] + " " + s[11:19]
    return s


def normalize_row(row) -> frozenset:
    """Convert a row to a frozenset of normalized values (column-order-independent)."""
    if isinstance(row, dict):
        return frozenset(normalize_value(v) for v in row.values())
    return frozenset(normalize_value(v) for v in row)


def execution_accurate(api_rows: list, golden_rows: list) -> bool:
    """True if every golden row can be matched to a unique API row (subset allowed).

    Uses O(n²) matching instead of sorted-zip so that extra columns in the
    generated SQL don't shift the sort key and cause wrong row pairings.
    """
    if not golden_rows and not api_rows:
        return True
    if len(api_rows) != len(golden_rows):
        return False
    api_norms  = [normalize_row(r) for r in api_rows]
    gold_norms = [normalize_row(r) for r in golden_rows]
    used = [False] * len(api_norms)
    for gold_row in gold_norms:
        matched = False
        for i, api_row in enumerate(api_norms):
            if not used[i] and (
                api_row == gold_row
                or gold_row.issubset(api_row)
                or api_row.issubset(gold_row)
            ):
                used[i] = True
                matched = True
                break
        if not matched:
            return False
    return True


def exact_match(generated_sql: str, golden_sql: str) -> bool:
    """True if sqlglot AST diff contains no structural changes."""
    try:
        gen  = sqlglot.parse_one(generated_sql, dialect="mysql")
        gold = sqlglot.parse_one(golden_sql, dialect="mysql")
        changes = [
            d for d in sqlglot.diff(gen, gold)
            if not isinstance(d, sqlglot.diff.Keep)
        ]
        return len(changes) == 0
    except Exception:
        return False


# ── Run evaluation ────────────────────────────────────────────
results = []
db = get_conn()

print(f"\nnl2sql Evaluation — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"API: {API_URL}")
print("=" * 72)

for tc in TEST_CASES:
    qid   = tc["id"]
    qtype = tc["query_type"]

    # 1. Call API
    try:
        resp = requests.post(
            API_URL,
            json={"question": tc["question"], "chat_history": []},
            timeout=30,
        )
        resp.raise_for_status()
        api_data = resp.json()
        api_rows     = api_data.get("table", [])
        generated_sql = api_data.get("sql", "")
        api_error    = api_data.get("error")
    except Exception as e:
        print(f"  [{qid}] API error: {e}")
        results.append({"id": qid, "query_type": qtype, "question": tc["question"],
                        "ex": False, "em": False, "error": str(e), "generated_sql": ""})
        continue

    # 2. Execute golden SQL
    try:
        with db.cursor() as cur:
            cur.execute(tc["golden_sql"])
            golden_rows = list(cur.fetchall())
    except Exception as e:
        print(f"  [{qid}] Golden SQL error: {e}")
        results.append({"id": qid, "query_type": qtype, "question": tc["question"],
                        "ex": False, "em": False, "error": f"golden: {e}", "generated_sql": generated_sql})
        continue

    # 3. Score
    ex = execution_accurate(api_rows, golden_rows) if not api_error else False
    em = exact_match(generated_sql, tc["golden_sql"]) if generated_sql else False

    status = "✓" if ex else "✗"
    em_str = "EM✓" if em else "   "
    api_n    = len(api_rows)
    gold_n   = len(golden_rows)
    row_info = f"api={api_n} gold={gold_n}" if not ex else f"rows={api_n}"
    print(f"  [{qid}] {status} {em_str}  {tc['question'][:55]}  ({row_info})")
    if args.verbose or (not ex and generated_sql):
        print(f"         Generated: {generated_sql[:120]}")
        if not ex and api_n == gold_n and api_n > 0:
            print(f"         API row 0:    {normalize_row(api_rows[0])}")
            print(f"         Golden row 0: {normalize_row(golden_rows[0])}")

    results.append({
        "id": qid,
        "query_type": qtype,
        "question": tc["question"],
        "ex": ex,
        "em": em,
        "error": api_error,
        "generated_sql": generated_sql,
    })

db.close()

# ── Aggregate scores ──────────────────────────────────────────
query_types = ["SELECT_SIMPLE", "SELECT_AGGREGATE", "SELECT_JOIN", "SELECT_TEMPORAL"]
type_results: dict[str, dict] = {}

for qt in query_types:
    subset = [r for r in results if r["query_type"] == qt]
    n = len(subset)
    ex_count = sum(1 for r in subset if r["ex"])
    em_count = sum(1 for r in subset if r["em"])
    type_results[qt] = {
        "n": n,
        "ex": ex_count,
        "em": em_count,
        "ex_pct": round(100 * ex_count / n, 1) if n else 0,
        "em_pct": round(100 * em_count / n, 1) if n else 0,
    }

total_n  = len(results)
total_ex = sum(1 for r in results if r["ex"])
total_em = sum(1 for r in results if r["em"])
overall_ex_pct = round(100 * total_ex / total_n, 1) if total_n else 0
overall_em_pct = round(100 * total_em / total_n, 1) if total_n else 0

print("\n" + "=" * 72)
print(f"{'Type':<22} {'EX':>6} {'EX%':>6}   {'EM':>6} {'EM%':>6}")
print("-" * 50)
for qt, s in type_results.items():
    print(f"  {qt:<20} {s['ex']:>3}/{s['n']}  {s['ex_pct']:>5.1f}%   {s['em']:>3}/{s['n']}  {s['em_pct']:>5.1f}%")
print("-" * 50)
print(f"  {'TOTAL':<20} {total_ex:>3}/{total_n}  {overall_ex_pct:>5.1f}%   {total_em:>3}/{total_n}  {overall_em_pct:>5.1f}%")
print()

threshold = 50.0
status_str = "PASS" if overall_ex_pct >= threshold else "FAIL"
print(f"  Execution Accuracy: {overall_ex_pct:.1f}%  — target ≥{threshold}%  [{status_str}]")
print()

# ── Write eval_report.md ──────────────────────────────────────
if args.report:
    report_path = os.path.join(os.path.dirname(__file__), "..", "docs", "eval_report.md")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Evaluation Report — nl2sql",
        f"\nGenerated: {ts}  |  API: {args.api}",
        "\n## Summary\n",
        f"| Metric | Score | Target |",
        f"|--------|-------|--------|",
        f"| Execution Accuracy (EX) | **{overall_ex_pct:.1f}%** ({total_ex}/{total_n}) | ≥ 50% |",
        f"| Exact Match Rate (EM)   | **{overall_em_pct:.1f}%** ({total_em}/{total_n}) | — |",
        f"| Overall result | **{status_str}** | — |",
        "\n## Per-Type Breakdown\n",
        "| Query Type | EX | EX% | EM | EM% |",
        "|------------|-----|-----|-----|-----|",
    ]
    for qt, s in type_results.items():
        lines.append(f"| {qt} | {s['ex']}/{s['n']} | {s['ex_pct']:.1f}% | {s['em']}/{s['n']} | {s['em_pct']:.1f}% |")

    lines += [
        "\n## Per-Query Results\n",
        "| ID | Type | Question | EX | EM | Error |",
        "|----|------|----------|----|----|-------|",
    ]
    for r in results:
        ex_icon = "✓" if r["ex"] else "✗"
        em_icon = "✓" if r["em"] else "✗"
        err     = r["error"] or ""
        q       = r["question"].replace("|", "\\|")
        lines.append(f"| {r['id']} | {r['query_type']} | {q} | {ex_icon} | {em_icon} | {err} |")

    lines += [
        "\n## Definitions",
        "\n- **Execution Accuracy (EX)**: The generated SQL returns the same result set as the golden SQL when run on the same database (rows compared after sorting and value normalization).",
        "- **Exact Match (EM)**: The generated SQL is structurally identical to the golden SQL according to `sqlglot.diff()` AST comparison.",
    ]

    with open(report_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  Report written to docs/eval_report.md")
