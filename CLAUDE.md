# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

`nl2sql` is a Text-to-SQL analytics engine for an e-commerce MySQL database. Users ask natural-language questions in a chat UI; the backend runs them through a 7-stage pipeline (Classify → SchemaLink → Retrieve → Generate → Validate → Execute → Format) and returns rows + a 1-2 sentence summary + an optional chart hint.

Two long-lived branches:
- **`main`** — native Mac dev target. Uses FAISS + sentence-transformers for example retrieval.
- **`feature/openshift`** — containerized OpenShift CRC target. Uses pure-Python BM25 instead of FAISS, and `mysql-connector-python` instead of `pymysql`. The swaps were forced because OpenShift CRC's Apple-Hypervisor VM SIGILLs (exit 132) on `cryptography._rust` and PyTorch ARM dispatch — see `docs/assignment_review.md` §5 for the full rationale before suggesting any retrieval/driver change.

## Common commands

### Backend (Python 3.12 + uv)
```bash
# Install / update lockfile
uv sync

# Dev server (from repo root or backend/)
cd backend && uv run uvicorn main:app --reload --port 8000

# Eval harness — runs 25 test queries, writes docs/eval_report.md
uv run python evaluation/eval.py --report
uv run python evaluation/eval.py --api http://localhost:8000 --verbose   # debug failing queries

# Seed scripts — only re-run if MySQL was wiped
uv run python database/seed_db.py
uv run python database/seed_examples.py --force
```

### Frontend (Next.js 15 + Node 20)
```bash
cd frontend
npm run dev      # dev server on :3000, hot reload
npm run build    # production build (used by Containerfile via output:"standalone")
npm run lint     # eslint
```

### Container build (from repo root, NOT from backend/ or frontend/)
```bash
podman build -f backend/Containerfile  -t quay.io/<org>/nl2sql-backend:<tag>  .
podman build -f frontend/Containerfile -t quay.io/<org>/nl2sql-frontend:<tag> .

# Pushing large layers to Quay reliably needs zstd:chunked
podman push --compression-format=zstd:chunked quay.io/<org>/nl2sql-backend:<tag>
```

### OpenShift deploy
```bash
oc apply -k deployment/k8s/                          # everything except seed job
oc apply -f deployment/k8s/jobs/seed-job.yaml -n nl2sql   # one-shot seed (idempotent enough)
oc set image deployment/nl2sql-backend  backend=quay.io/<org>/nl2sql-backend:<tag>  -n nl2sql
oc set image deployment/nl2sql-frontend frontend=quay.io/<org>/nl2sql-frontend:<tag> -n nl2sql
```

`deployment/k8s/secret.yaml` is **gitignored** (real creds live in `backend/.env.local`). The committed `secret.example.yaml` is the template. Apply real secrets with: `oc create secret generic nl2sql-secret --from-env-file=backend/.env.local -n nl2sql`.

## Architecture

### Pipeline (single request flow)

The whole HTTP path is `backend/app/api/routes/query.py`. It calls each stage in order; every stage has a typed Pydantic input/output in `backend/app/models/schemas.py`. Stages are pure functions, callable independently for testing.

```
question → classify_query → link_schema → retrieve_examples → generate_sql
        → validate_sql → execute_sql → [retry once on failure] → format_result
        → [optional] sqlglot.transpile() for non-mysql dialect → log to query_logs
```

**Self-healing retry** (lines 50-65 of `query.py`): if execution fails, the error message + failing SQL are re-injected into a prompt, Claude returns a corrected query, that gets re-validated and re-executed once. Don't add a second retry — it leads to degenerate loops.

**Multi-dialect display**: `model_config.dialect` is read after execution and, if set to anything except `mysql`, `sqlglot.transpile()` produces a second SQL string for the UI. Generation always stays in MySQL since that's the actual DB. The mapping from admin-UI labels (`postgresql`, `mssql`) to sqlglot dialect names (`postgres`, `tsql`) lives in `_SQLGLOT_DIALECT` in `query.py`.

### Three "teaching" surfaces — defense in depth and prompt control

The admin UI has 5 panels, but only three of them shape Claude's behavior at query time:

| Panel | Backing table | What injects into Claude's prompt | Effect |
|---|---|---|---|
| Schema Manager | `schema_metadata` | Per-column descriptions + sensitive flag | Removes ambiguity ("`orders.total` includes tax"), hides PII columns from the LLM |
| Examples Manager | `few_shot_examples` | Top-3 BM25-matched Q→SQL pairs | Pattern-matches new questions against curated examples; rebuilds index on every CRUD via `build_faiss_index()` (legacy name kept) |
| Guardrails Config | `guardrails` | Nothing (consumed by Validator only) | Last-mile keyword block on generated SQL |

**Guardrails are layer 3 of 4.** Layers 1-4 in order: Classifier returns `UNSUPPORTED` for non-SELECT intents → Generator prompt says SELECT-only → Validator keyword check (this is the toggle) → Executor uses read-only DB user. Toggling INSERT to "Allowed" only relaxes layer 3 — layers 1, 2, 4 still block writes. The Guardrails admin page has an explanatory amber notice describing this.

### Frontend → Backend wiring

The Next.js standalone container does **not** talk to the backend over the OpenShift Route. The browser fetches relative paths (`/api/v1/query`), the Next.js server applies a rewrite to `${BACKEND_URL}/api/v1/*`, and Next.js proxies server-to-server.

Critical: `BACKEND_URL` is **read at build time** by `next.config.ts`, not runtime. Setting it in the Pod env does nothing — the Containerfile bakes `ENV BACKEND_URL=http://nl2sql-backend:8000` before `npm run build`. If you change the backend service name, rebuild the frontend image.

`NEXT_PUBLIC_API_URL=""` (also build-time) makes the browser fetch relative URLs. The fallback `?? ""` (not `?? "http://localhost:8000"`) is required — empty string keeps things relative; localhost would break the deployed app.

### Database connections — two SQLAlchemy engines

`backend/app/core/database.py` exposes both:
- `engine` (full read/write) — used by admin endpoints to mutate config tables
- `engine_readonly` — used by the SQL Executor stage. The `db_readonly_user` MySQL account has `SELECT` only. This is the 4th guardrail layer; do not change the executor to use the write engine.

### OpenShift-specific quirks

- **Arbitrary UID**: backend Containerfile does `chown -R 1001:0 /app && chmod -R g=u /app` so it runs under any random UID OpenShift assigns.
- **`.containerignore`** at repo root excludes `backend/.env.local` from images. Do not remove it — leaking real creds into a public Quay image is the failure mode.
- **CRC SIGILL**: any new dependency that pulls `cryptography`, `numpy`-with-SVE, or PyTorch will exit 132 inside CRC's VM. Verify with `oc apply -f deployment/k8s/jobs/debug-pod.yaml` (a one-shot pod that imports each suspect package and prints its name on success). Pure-Python alternatives are preferred on `feature/openshift`.

### Frontend (Next.js 15) — read this before editing UI

This Next.js version has breaking changes from training-data versions. Always check `frontend/node_modules/next/dist/docs/` for the actual current API before writing code. Especially:
- App Router conventions (`app/` not `pages/`, server vs client components)
- `next.config.ts` (TypeScript config, `output: "standalone"`, `rewrites()` runs at build time)
- Tailwind v4 class names

## Eval harness gotchas

`evaluation/eval.py` does its own DB connection (bypasses the backend) to run golden SQL. Both `--api` (backend URL) and a working DB connection (via env vars) are required. The harness intentionally does **column-agnostic frozenset matching** with 2-decimal float rounding and `T`→space datetime normalization — the LLM often returns extra columns, and exact tuple matching would massively under-report accuracy. If a test fails, run `--verbose` to see generated SQL + first row diff before assuming the test is wrong.

For OpenShift, port-forward both services:
```bash
oc port-forward service/nl2sql-backend 8000:8000 -n nl2sql   # terminal 1
oc port-forward service/mysql           3306:3306 -n nl2sql   # terminal 2
uv run python evaluation/eval.py --api http://localhost:8000 --report
```

CRC runs slow under load — bump the eval `requests` timeout in `eval.py` (currently 90s) if pods restart mid-run.
