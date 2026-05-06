# nl2sql — Natural Language to SQL Analytics Engine

Ask plain-English questions about an e-commerce database. Claude Sonnet generates the SQL, executes it, and returns a summary, sortable table, auto chart, and the SQL itself.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Claude Sonnet (Anthropic) via LangChain |
| Backend | FastAPI + SQLAlchemy + uvicorn |
| Vector search | FAISS + sentence-transformers |
| Database | MySQL 8 |
| Frontend | Next.js 15 + Tailwind CSS + TanStack Table + Recharts |
| Observability | LangSmith |
| Runtime | Python 3.12 via `uv` |

---

## Prerequisites

- Python 3.12 (`uv` installed)
- Node.js 20 + npm
- MySQL 8 running locally
- Anthropic API key

---

## Setup

### 1. Clone and enter the project

```bash
git clone <repo> nl2sql
cd nl2sql
```

### 2. Create MySQL database and users

```sql
CREATE DATABASE nl2sql CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'nl2sql_user'@'localhost' IDENTIFIED BY 'user';
GRANT ALL PRIVILEGES ON nl2sql.* TO 'nl2sql_user'@'localhost';

CREATE USER 'nl2sql_readonly'@'localhost' IDENTIFIED BY 'readonlypassword';
GRANT SELECT ON nl2sql.* TO 'nl2sql_readonly'@'localhost';

FLUSH PRIVILEGES;
```

### 3. Apply schema

```bash
mysql -u nl2sql_user -p nl2sql < database/schema.sql
```

### 4. Configure environment

Copy and edit `backend/.env.local`:

```bash
cp backend/.env.local.example backend/.env.local   # or edit directly
```

Required env vars:

| Variable | Description |
|----------|-------------|
| `DB_HOST` | MySQL host (default: `localhost`) |
| `DB_PORT` | MySQL port (default: `3306`) |
| `DB_USER` | Full-access user |
| `DB_PASSWORD` | Full-access password |
| `DB_NAME` | Database name (`nl2sql`) |
| `DB_READONLY_USER` | Read-only user for SQL Executor |
| `DB_READONLY_PASSWORD` | Read-only password |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `LANGCHAIN_API_KEY` | LangSmith key (optional, for tracing) |
| `LANGCHAIN_PROJECT` | LangSmith project name |

### 5. Seed the database

```bash
# Install Python deps
uv sync

# Seed e-commerce data (500 customers, 50 products, 2000 orders, etc.)
uv run python database/seed_db.py

# Seed 30 Q→SQL few-shot examples into FAISS
uv run python database/seed_examples.py
```

### 6. Start the backend

```bash
cd backend
uv run uvicorn main:app --reload --port 8000
```

Backend available at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### 7. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at `http://localhost:3000`.

---

## Usage

### Chat UI (`http://localhost:3000`)

Type a question in plain English. The system:
1. Classifies intent (SIMPLE / AGGREGATE / JOIN / TEMPORAL / UNSUPPORTED)
2. Retrieves the 3 most similar Q→SQL examples via FAISS
3. Links natural language entities to real schema columns
4. Generates SQL with Claude Sonnet
5. Validates (syntax + blocklist) and executes against read-only DB
6. Returns a plain-English summary, sortable data table, auto chart (when applicable), and collapsible SQL preview

Conversation history (last 6 messages) is sent on each query for multi-turn context.

### Sample queries to try

```
How many customers do we have?
Top 5 customers by total spending
Monthly revenue for the last 12 months
Show products with zero stock
Which orders are still pending?
Revenue breakdown by product category
Show reviews with customer and product names
```

### Admin panel (`http://localhost:3000/admin`)

| Panel | Path | Purpose |
|-------|------|---------|
| Schema Manager | `/admin/schema` | Edit column descriptions, mark sensitive columns |
| Examples Manager | `/admin/examples` | Add / edit / delete Q→SQL few-shot pairs |
| Query Logs | `/admin/logs` | Browse all queries, filter by status/type, export CSV |
| Guardrails Config | `/admin/guardrails` | Block/allow SQL operations (DROP, DELETE, etc.) |
| Model Config | `/admin/config` | LLM provider, model, temperature, dialect, max tokens |

---

## API Reference

### `POST /api/v1/query`

```json
{
  "question": "Top 5 customers by revenue",
  "chat_history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

Response:

```json
{
  "nl_summary": "The top customer is ...",
  "table": [...],
  "columns": ["name", "total_spent"],
  "sql": "SELECT ...",
  "query_type": "SELECT_JOIN",
  "row_count": 5,
  "latency_ms": 342.1,
  "chart_type": "bar",
  "error": null
}
```

`chart_type` is `"bar"` | `"line"` | `null` — set automatically when the result has exactly 2 columns and the second is numeric.

---

## Evaluation

Run with the backend running:

```bash
# Print results to terminal
uv run python evaluation/eval.py

# Also write docs/eval_report.md
uv run python evaluation/eval.py --report
```

Evaluates 25 test queries across 4 types:

| Metric | Definition |
|--------|-----------|
| Execution Accuracy (EX) | Generated result set matches golden SQL result set |
| Exact Match (EM) | Generated SQL is AST-identical to golden SQL (sqlglot.diff) |

Target: **≥ 50% Execution Accuracy** overall.

---

## Project Structure

```
nl2sql/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # FastAPI routers (query + 5 admin)
│   │   ├── core/                # Config, DB engine, init_db
│   │   ├── models/              # SQLAlchemy models + Pydantic schemas
│   │   └── pipeline/            # 7-step NL→SQL pipeline
│   ├── main.py                  # FastAPI app, CORS, lifespan
│   └── .env.local               # Environment config (not committed)
├── frontend/
│   └── app/
│       ├── components/          # MessageBubble, ResultsTable, ResultChart, etc.
│       ├── admin/               # 5 admin panel pages
│       └── lib/                 # Shared TypeScript types
├── database/
│   ├── schema.sql               # MySQL DDL (6 tables)
│   ├── seed_db.py               # Seed 500 customers, 2000 orders, etc.
│   └── seed_examples.py         # Seed 30 Q→SQL few-shot pairs
├── docs/
│   ├── data_dictionary.md       # Table/column descriptions
│   ├── test_queries.md          # 25 test queries with golden SQL
│   └── eval_report.md           # Auto-generated by eval.py --report
└── evaluation/
    └── eval.py                  # Evaluation harness (EX + EM)
```

---

## Known Limitations

- **Single dialect**: Tested against MySQL 8 only. PostgreSQL/SQLite dialects can be selected in Model Config but are not validated against a live DB.
- **FAISS not persisted**: The FAISS index is rebuilt in memory at every backend startup from the `few_shot_examples` table. Startup takes a few seconds with 30+ examples.
- **No auth**: Admin panel and API have no authentication. Do not expose to the internet.
- **Ambiguous revenue column**: `orders.total` includes tax and shipping. `order_items.subtotal` is item-only revenue. Queries about "revenue" may return different numbers depending on which column Claude chooses.
- **Temporal queries depend on seed data**: Queries like "orders this month" may return zero rows if the seed script did not generate orders in the current month.
- **Rate limits**: Each query makes 2–3 Claude API calls (classifier + generator + formatter). Heavy eval runs may hit Anthropic rate limits.
