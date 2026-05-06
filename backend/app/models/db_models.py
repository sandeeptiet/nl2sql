from sqlalchemy import (
    Column, Integer, String, Text,
    DateTime, Boolean, Float, Enum as SAEnum
)
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class QueryLog(Base):
    __tablename__ = "query_logs"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    nl_input     = Column(Text, nullable=False)
    generated_sql= Column(Text)
    query_type   = Column(String(50))
    status       = Column(String(20))   # success | error
    latency_ms   = Column(Float)
    row_count    = Column(Integer)
    error_msg    = Column(Text)
    created_at   = Column(DateTime, server_default=func.now())

class FewShotExample(Base):
    __tablename__ = "few_shot_examples"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    question     = Column(Text, nullable=False)
    sql          = Column(Text, nullable=False)
    query_type   = Column(String(50))
    created_at   = Column(DateTime, server_default=func.now())
    updated_at   = Column(DateTime, server_default=func.now(),
                          onupdate=func.now())

class SchemaMetadata(Base):
    __tablename__ = "schema_metadata"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    table_name   = Column(String(100), nullable=False)
    column_name  = Column(String(100), nullable=False)
    description  = Column(Text)
    is_sensitive = Column(Boolean, default=False)

class Guardrail(Base):
    __tablename__ = "guardrails"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    operation    = Column(String(50), nullable=False, unique=True)
    is_blocked   = Column(Boolean, default=True)

class ModelConfig(Base):
    __tablename__ = "model_config"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    llm_provider = Column(String(50), default="anthropic")
    model_name   = Column(String(100), default="claude-sonnet-4-6")
    temperature  = Column(Float, default=0.0)
    dialect      = Column(String(20), default="mysql")
    max_tokens   = Column(Integer, default=1000)