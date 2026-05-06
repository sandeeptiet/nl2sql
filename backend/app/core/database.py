from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import get_settings

settings = get_settings()

# Full access engine — used by admin, schema linker
engine = create_engine(
    settings.db_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Read-only engine — used by SQL Executor only
readonly_engine = create_engine(
    settings.db_readonly_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
ReadOnlySession = sessionmaker(bind=readonly_engine, autocommit=False, autoflush=False)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_readonly_db():
    db = ReadOnlySession()
    try:
        yield db
    finally:
        db.close()