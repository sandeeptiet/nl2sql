# Evaluation Report — nl2sql

Generated: 2026-05-06 14:50  |  API: http://localhost:8000

## Summary

| Metric | Score | Target |
|--------|-------|--------|
| Execution Accuracy (EX) | **68.0%** (17/25) | ≥ 50% |
| Exact Match Rate (EM)   | **0.0%** (0/25) | — |
| Overall result | **PASS** | — |

## Per-Type Breakdown

| Query Type | EX | EX% | EM | EM% |
|------------|-----|-----|-----|-----|
| SELECT_SIMPLE | 6/6 | 100.0% | 0/6 | 0.0% |
| SELECT_AGGREGATE | 5/6 | 83.3% | 0/6 | 0.0% |
| SELECT_JOIN | 5/7 | 71.4% | 0/7 | 0.0% |
| SELECT_TEMPORAL | 1/6 | 16.7% | 0/6 | 0.0% |

## Per-Query Results

| ID | Type | Question | EX | EM | Error |
|----|------|----------|----|----|-------|
| S1 | SELECT_SIMPLE | Which products are currently in stock? | ✓ | ✗ |  |
| S2 | SELECT_SIMPLE | Show all processing orders | ✓ | ✗ |  |
| S3 | SELECT_SIMPLE | List all product categories | ✓ | ✗ |  |
| S4 | SELECT_SIMPLE | Show products priced above 5000 | ✓ | ✗ |  |
| S5 | SELECT_SIMPLE | List all 1-star reviews | ✓ | ✗ |  |
| S6 | SELECT_SIMPLE | Show all delivered orders | ✓ | ✗ |  |
| A1 | SELECT_AGGREGATE | How many total customers are there? | ✓ | ✗ |  |
| A2 | SELECT_AGGREGATE | What is the total revenue? | ✓ | ✗ |  |
| A3 | SELECT_AGGREGATE | What is the average order value? | ✗ | ✗ |  |
| A4 | SELECT_AGGREGATE | How many orders per status? | ✓ | ✗ |  |
| A5 | SELECT_AGGREGATE | What is the average product rating? | ✓ | ✗ |  |
| A6 | SELECT_AGGREGATE | What is the most expensive product? | ✓ | ✗ |  |
| J1 | SELECT_JOIN | Show all orders with customer details | ✓ | ✗ |  |
| J2 | SELECT_JOIN | List all products with their category | ✓ | ✗ |  |
| J3 | SELECT_JOIN | Top 5 customers by total spending | ✓ | ✗ |  |
| J4 | SELECT_JOIN | Find customers with no orders | ✓ | ✗ |  |
| J5 | SELECT_JOIN | Top 5 products by units sold | ✗ | ✗ |  |
| J6 | SELECT_JOIN | Revenue breakdown by product category | ✓ | ✗ |  |
| J7 | SELECT_JOIN | Show reviews with customer and product names | ✗ | ✗ |  |
| T1 | SELECT_TEMPORAL | What orders were placed in the last month? | ✓ | ✗ |  |
| T2 | SELECT_TEMPORAL | Show monthly revenue for the past year | ✗ | ✗ | HTTPConnectionPool(host='localhost', port=8000): Read timed out. (read timeout=30) |
| T3 | SELECT_TEMPORAL | How many new customers signed up this month? | ✗ | ✗ | HTTPConnectionPool(host='localhost', port=8000): Read timed out. (read timeout=30) |
| T4 | SELECT_TEMPORAL | Orders from the past week that were delivered | ✗ | ✗ | HTTPConnectionPool(host='localhost', port=8000): Read timed out. (read timeout=30) |
| T5 | SELECT_TEMPORAL | How many orders were placed each month in 2024? | ✗ | ✗ | HTTPConnectionPool(host='localhost', port=8000): Read timed out. (read timeout=30) |
| T6 | SELECT_TEMPORAL | Show customers who joined in the last 3 months | ✗ | ✗ | HTTPConnectionPool(host='localhost', port=8000): Read timed out. (read timeout=30) |

## Definitions

- **Execution Accuracy (EX)**: The generated SQL returns the same result set as the golden SQL when run on the same database (rows compared after sorting and value normalization).
- **Exact Match (EM)**: The generated SQL is structurally identical to the golden SQL according to `sqlglot.diff()` AST comparison.
