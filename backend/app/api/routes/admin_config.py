from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.db_models import ModelConfig
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ConfigUpdate(BaseModel):
    llm_provider: Optional[str] = None
    model_name:   Optional[str] = None
    temperature:  Optional[float] = None
    dialect:      Optional[str] = None
    max_tokens:   Optional[int] = None

def get_or_create_config(db: Session) -> ModelConfig:
    config = db.query(ModelConfig).first()
    if not config:
        config = ModelConfig()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

@router.get("/config")
def get_config(db: Session = Depends(get_db)):
    config = get_or_create_config(db)
    return {
        "llm_provider": config.llm_provider,
        "model_name":   config.model_name,
        "temperature":  config.temperature,
        "dialect":      config.dialect,
        "max_tokens":   config.max_tokens,
    }

@router.put("/config")
def update_config(
    payload: ConfigUpdate,
    db: Session = Depends(get_db)
):
    config = get_or_create_config(db)
    if payload.llm_provider is not None:
        config.llm_provider = payload.llm_provider  # type: ignore[assignment]
    if payload.model_name is not None:
        config.model_name   = payload.model_name    # type: ignore[assignment]
    if payload.temperature is not None:
        config.temperature  = payload.temperature   # type: ignore[assignment]
    if payload.dialect is not None:
        config.dialect      = payload.dialect       # type: ignore[assignment]
    if payload.max_tokens is not None:
        config.max_tokens   = payload.max_tokens    # type: ignore[assignment]
    db.commit()
    return {"status": "updated"}