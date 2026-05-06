# Test Queries — nl2sql

25 natural language queries across 4 types used for demo showcase and evaluation.
Golden SQL is valid MySQL 8.0 against the seeded e-commerce schema.

---

## SELECT_SIMPLE (6)

| # | Question | Golden SQL |
|---|----------|------------|
| S1 | Which products are currently in stock? | `SELECT id, name, price, stock FROM products WHERE stock > 0 AND is_active = 1 LIMIT 100` |
| S2 | Show all processing orders | `SELECT id, customer_id, total, created_at FROM orders WHERE status = 'processing' LIMIT 100` |
| S3 | List all product categories | `SELECT id, name FROM categories LIMIT 100` |
| S4 | Show products priced above 5000 | `SELECT id, name, price FROM products WHERE price > 5000 LIMIT 100` |
| S5 | List all 1-star reviews | `SELECT id, product_id, customer_id, comment, created_at FROM reviews WHERE rating = 1 LIMIT 100` |
| S6 | Show all delivered orders | `SELECT id, customer_id, total, delivered_at FROM orders WHERE status = 'delivered' LIMIT 100` |

---

## SELECT_AGGREGATE (6)

| # | Question | Golden SQL |
|---|----------|------------|
| A1 | How many total customers are there? | `SELECT COUNT(*) AS total_customers FROM customers` |
| A2 | What is the total revenue? | `SELECT SUM(total) AS total_revenue FROM orders WHERE status != 'cancelled'` |
| A3 | What is the average order value? | `SELECT AVG(total) AS avg_order_value FROM orders WHERE status != 'cancelled'` |
| A4 | How many orders per status? | `SELECT status, COUNT(*) AS order_count FROM orders GROUP BY status ORDER BY order_count DESC LIMIT 100` |
| A5 | What is the average product rating? | `SELECT AVG(rating) AS avg_rating FROM reviews` |
| A6 | What is the most expensive product? | `SELECT name, price FROM products ORDER BY price DESC LIMIT 1` |

---

## SELECT_JOIN (7)

| # | Question | Golden SQL |
|---|----------|------------|
| J1 | Show all orders with customer details | `SELECT o.id, c.name, c.email, o.status, o.total, o.created_at FROM orders o JOIN customers c ON o.customer_id = c.id ORDER BY o.created_at DESC LIMIT 100` |
| J2 | List all products with their category | `SELECT p.name, c.name AS category, p.price FROM products p JOIN categories c ON p.category_id = c.id LIMIT 100` |
| J3 | Top 5 customers by total spending | `SELECT c.name, c.email, SUM(o.total) AS total_spent FROM customers c JOIN orders o ON c.id = o.customer_id WHERE o.status != 'cancelled' GROUP BY c.id, c.name, c.email ORDER BY total_spent DESC LIMIT 5` |
| J4 | Find customers with no orders | `SELECT c.id, c.name, c.email FROM customers c LEFT JOIN orders o ON c.id = o.customer_id WHERE o.id IS NULL LIMIT 100` |
| J5 | Top 5 products by units sold | `SELECT p.name, SUM(oi.quantity) AS total_sold FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.id, p.name ORDER BY total_sold DESC LIMIT 5` |
| J6 | Revenue breakdown by product category | `SELECT c.name AS category, SUM(oi.subtotal) AS revenue FROM order_items oi JOIN products p ON oi.product_id = p.id JOIN categories c ON p.category_id = c.id GROUP BY c.name ORDER BY revenue DESC LIMIT 100` |
| J7 | Show reviews with customer and product names | `SELECT c.name AS customer, p.name AS product, r.rating, r.created_at FROM reviews r JOIN customers c ON r.customer_id = c.id JOIN products p ON r.product_id = p.id LIMIT 100` |

---

## SELECT_TEMPORAL (6)

| # | Question | Golden SQL |
|---|----------|------------|
| T1 | What orders were placed in the last month? | `SELECT id, status, total, created_at FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) ORDER BY created_at DESC LIMIT 100` |
| T2 | Show monthly revenue for the past year | `SELECT DATE_FORMAT(created_at, '%Y-%m') AS month, SUM(total) AS revenue FROM orders WHERE status != 'cancelled' AND created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH) GROUP BY month ORDER BY month LIMIT 100` |
| T3 | How many new customers signed up this month? | `SELECT COUNT(*) AS new_customers FROM customers WHERE YEAR(created_at) = YEAR(CURDATE()) AND MONTH(created_at) = MONTH(CURDATE())` |
| T4 | Orders from the past week that were delivered | `SELECT id, customer_id, total, delivered_at FROM orders WHERE status = 'delivered' AND delivered_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) LIMIT 100` |
| T5 | How many orders were placed each month in 2024? | `SELECT DATE_FORMAT(created_at, '%Y-%m') AS month, COUNT(*) AS order_count FROM orders WHERE YEAR(created_at) = 2024 GROUP BY month ORDER BY month LIMIT 100` |
| T6 | Show customers who joined in the last 3 months | `SELECT id, name, email, created_at FROM customers WHERE created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY) ORDER BY created_at DESC LIMIT 100` |
