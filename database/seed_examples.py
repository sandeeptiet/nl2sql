"""
Seed 30 Q→SQL few-shot examples into few_shot_examples table.
Run once before starting the backend so FAISS is pre-loaded.

Usage:
    cd /path/to/nl2sql
    uv run python database/seed_examples.py          # skip if rows exist
    uv run python database/seed_examples.py --force  # replace all
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env.local"))

import pymysql

parser = argparse.ArgumentParser()
parser.add_argument("--force", action="store_true", help="Delete existing examples and reseed")
args = parser.parse_args()

conn = pymysql.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", ""),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", ""),
    charset="utf8mb4",
)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM few_shot_examples")
existing = cur.fetchone()[0]  # type: ignore[index]

if existing > 0 and not args.force:
    print(f"  {existing} examples already exist. Use --force to reseed.")
    cur.close()
    conn.close()
    sys.exit(0)

if args.force:
    cur.execute("DELETE FROM few_shot_examples")
    conn.commit()
    print("  Cleared existing examples.")

# ── 8 SELECT_SIMPLE ───────────────────────────────────────────
SIMPLE = [
    (
        "Show me all active products",
        "SELECT id, name, price, stock FROM products WHERE is_active = 1 LIMIT 100",
    ),
    (
        "List all pending orders",
        "SELECT id, customer_id, total, created_at FROM orders WHERE status = 'pending' LIMIT 100",
    ),
    (
        "What are all the product categories?",
        "SELECT id, name, description FROM categories LIMIT 100",
    ),
    (
        "Show all products with zero stock",
        "SELECT id, name, price FROM products WHERE stock = 0 LIMIT 100",
    ),
    (
        "List all cancelled orders",
        "SELECT id, customer_id, total, created_at FROM orders WHERE status = 'cancelled' LIMIT 100",
    ),
    (
        "Show all 5-star reviews",
        "SELECT id, product_id, customer_id, comment, created_at FROM reviews WHERE rating = 5 LIMIT 100",
    ),
    (
        "List all shipped orders",
        "SELECT id, customer_id, total, created_at FROM orders WHERE status = 'shipped' LIMIT 100",
    ),
    (
        "Show all inactive products",
        "SELECT id, name, price FROM products WHERE is_active = 0 LIMIT 100",
    ),
]

# ── 8 SELECT_AGGREGATE ────────────────────────────────────────
AGGREGATE = [
    (
        "How many customers do we have?",
        "SELECT COUNT(*) AS total_customers FROM customers",
    ),
    (
        "What is the total revenue from all non-cancelled orders?",
        "SELECT SUM(total) AS total_revenue FROM orders WHERE status != 'cancelled'",
    ),
    (
        "What is the average order value?",
        "SELECT AVG(total) AS avg_order_value FROM orders WHERE status != 'cancelled'",
    ),
    (
        "How many orders are there per status?",
        "SELECT status, COUNT(*) AS order_count FROM orders GROUP BY status ORDER BY order_count DESC LIMIT 100",
    ),
    (
        "What is the average rating across all reviews?",
        "SELECT AVG(rating) AS avg_rating FROM reviews",
    ),
    (
        "What is the highest-priced product?",
        "SELECT name, price FROM products ORDER BY price DESC LIMIT 1",
    ),
    (
        "How many reviews does each product have?",
        "SELECT product_id, COUNT(*) AS review_count FROM reviews GROUP BY product_id ORDER BY review_count DESC LIMIT 100",
    ),
    (
        "What is the total number of orders?",
        "SELECT COUNT(*) AS total_orders FROM orders",
    ),
]

# ── 8 SELECT_JOIN ─────────────────────────────────────────────
JOIN = [
    (
        "Show orders with customer names",
        "SELECT o.id, c.name AS customer, o.status, o.total, o.created_at FROM orders o JOIN customers c ON o.customer_id = c.id ORDER BY o.created_at DESC LIMIT 100",
    ),
    (
        "Show all products with their category names",
        "SELECT p.id, p.name, c.name AS category, p.price, p.stock FROM products p JOIN categories c ON p.category_id = c.id LIMIT 100",
    ),
    (
        "Top 5 customers by total amount spent",
        "SELECT c.name, c.email, SUM(o.total) AS total_spent FROM customers c JOIN orders o ON c.id = o.customer_id WHERE o.status != 'cancelled' GROUP BY c.id, c.name, c.email ORDER BY total_spent DESC LIMIT 5",
    ),
    (
        "Customers who have never placed an order",
        "SELECT c.id, c.name, c.email FROM customers c LEFT JOIN orders o ON c.id = o.customer_id WHERE o.id IS NULL LIMIT 100",
    ),
    (
        "Show reviews with customer name and product name",
        "SELECT r.id, c.name AS customer, p.name AS product, r.rating, r.comment FROM reviews r JOIN customers c ON r.customer_id = c.id JOIN products p ON r.product_id = p.id LIMIT 100",
    ),
    (
        "Top 5 best-selling products by quantity sold",
        "SELECT p.name, SUM(oi.quantity) AS total_sold FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.id, p.name ORDER BY total_sold DESC LIMIT 5",
    ),
    (
        "Total revenue per product category",
        "SELECT c.name AS category, SUM(oi.subtotal) AS revenue FROM order_items oi JOIN products p ON oi.product_id = p.id JOIN categories c ON p.category_id = c.id GROUP BY c.name ORDER BY revenue DESC LIMIT 100",
    ),
    (
        "Show products with their average rating",
        "SELECT p.name, ROUND(AVG(r.rating), 2) AS avg_rating, COUNT(r.id) AS review_count FROM products p LEFT JOIN reviews r ON p.id = r.product_id GROUP BY p.id, p.name ORDER BY avg_rating DESC LIMIT 100",
    ),
]

# ── 6 SELECT_TEMPORAL ─────────────────────────────────────────
TEMPORAL = [
    (
        "Orders placed in the last 30 days",
        "SELECT id, customer_id, status, total, created_at FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) ORDER BY created_at DESC LIMIT 100",
    ),
    (
        "Monthly revenue for the last 12 months",
        "SELECT DATE_FORMAT(created_at, '%Y-%m') AS month, SUM(total) AS revenue FROM orders WHERE status != 'cancelled' AND created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH) GROUP BY month ORDER BY month LIMIT 100",
    ),
    (
        "New customers registered this month",
        "SELECT id, name, email, city, created_at FROM customers WHERE YEAR(created_at) = YEAR(CURDATE()) AND MONTH(created_at) = MONTH(CURDATE()) ORDER BY created_at DESC LIMIT 100",
    ),
    (
        "Orders delivered in the last 7 days",
        "SELECT o.id, c.name AS customer, o.total, o.delivered_at FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.status = 'delivered' AND o.delivered_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) ORDER BY o.delivered_at DESC LIMIT 100",
    ),
    (
        "Monthly order count for 2024",
        "SELECT DATE_FORMAT(created_at, '%Y-%m') AS month, COUNT(*) AS order_count FROM orders WHERE YEAR(created_at) = 2024 GROUP BY month ORDER BY month LIMIT 100",
    ),
    (
        "Customers who registered in the last 90 days",
        "SELECT id, name, email, city, created_at FROM customers WHERE created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY) ORDER BY created_at DESC LIMIT 100",
    ),
]

rows = (
    [(q, s, "SELECT_SIMPLE")    for q, s in SIMPLE]
    + [(q, s, "SELECT_AGGREGATE") for q, s in AGGREGATE]
    + [(q, s, "SELECT_JOIN")      for q, s in JOIN]
    + [(q, s, "SELECT_TEMPORAL")  for q, s in TEMPORAL]
)

cur.executemany(
    "INSERT INTO few_shot_examples (question, `sql`, query_type) VALUES (%s, %s, %s)",
    rows,
)
conn.commit()
print(f"  Inserted {len(rows)} few-shot examples.")
print("  Restart the backend to rebuild the FAISS index.")

cur.close()
conn.close()
