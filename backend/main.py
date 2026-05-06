from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api.routes.query import router as query_router
from app.pipeline.retriever import build_faiss_index
from app.core.init_db import init_db
from app.api.routes.admin_schema import router as schema_router
from app.api.routes.admin_examples import router as examples_router
from app.api.routes.admin_logs import router as logs_router
from app.api.routes.admin_guardrails import router as guardrails_router
from app.api.routes.admin_config import router as config_router

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    build_faiss_index()
    yield

app = FastAPI(
    title="nl2sql",
    description="Natural Language to SQL Analytics Engine",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(query_router, prefix="/api/v1")

# admin
app.include_router(schema_router,     prefix="/api/v1/admin")
app.include_router(examples_router,   prefix="/api/v1/admin")
app.include_router(logs_router,       prefix="/api/v1/admin")
app.include_router(guardrails_router, prefix="/api/v1/admin")
app.include_router(config_router,     prefix="/api/v1/admin")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "env": settings.app_env,
        "project": "nl2sql"
    }