from pydantic import BaseModel
from typing import Optional, List, Any
from enum import Enum

class QueryType(str, Enum):
    SELECT_SIMPLE     = "SELECT_SIMPLE"
    SELECT_AGGREGATE  = "SELECT_AGGREGATE"
    SELECT_JOIN       = "SELECT_JOIN"
    SELECT_TEMPORAL   = "SELECT_TEMPORAL"
    UNSUPPORTED       = "UNSUPPORTED"

# ── pipeline component models ─────────────────────────────────

class ClassifierOutput(BaseModel):
    query_type: QueryType
    tables_mentioned: List[str]
    columns_mentioned: List[str]
    reason: str

class SchemaColumn(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    is_sensitive: bool = False

class SchemaTable(BaseModel):
    name: str
    columns: List[SchemaColumn]

class LinkerOutput(BaseModel):
    resolved_tables: List[str]
    resolved_columns: List[str]
    ambiguities: List[str]
    schema_context: str   # formatted string injected into prompt

class Example(BaseModel):
    question: str
    sql: str
    query_type: Optional[str] = None

class RetrieverOutput(BaseModel):
    examples: List[Example]

class GeneratorOutput(BaseModel):
    sql: str
    explanation: str

class ValidatorOutput(BaseModel):
    valid: bool
    sanitized_sql: str
    errors: List[str]

class ExecutorOutput(BaseModel):
    rows: List[dict]
    columns: List[str]
    row_count: int
    latency_ms: float
    error: Optional[str] = None

class FormatterOutput(BaseModel):
    table: List[dict]
    columns: List[str]
    nl_summary: str
    chart_type: Optional[str] = None  # 'bar' | 'line' | None

# ── API request / response ────────────────────────────────────

class ChatMessage(BaseModel):
    role: str   # 'user' | 'assistant'
    content: str

class QueryRequest(BaseModel):
    question: str
    chat_history: Optional[List[ChatMessage]] = []

class QueryResponse(BaseModel):
    nl_summary: str
    table: List[dict]
    columns: List[str]
    sql: str
    query_type: str
    row_count: int
    latency_ms: float
    chart_type: Optional[str] = None
    error: Optional[str] = None