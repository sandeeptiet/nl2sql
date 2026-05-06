from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.db_models import Guardrail
from pydantic import BaseModel
from typing import List

router = APIRouter()

DEFAULT_OPERATIONS = [
    "DROP", "DELETE", "UPDATE",
    "INSERT", "TRUNCATE", "ALTER"
]

class GuardrailUpdate(BaseModel):
    operation:  str
    is_blocked: bool

def seed_guardrails(db: Session):
    """Ensure default guardrail rows exist on first run."""
    for op in DEFAULT_OPERATIONS:
        exists = db.query(Guardrail).filter_by(operation=op).first()
        if not exists:
            db.add(Guardrail(operation=op, is_blocked=True))
    db.commit()

@router.get("/guardrails")
def get_guardrails(db: Session = Depends(get_db)):
    seed_guardrails(db)
    rules = db.query(Guardrail).all()
    return {"guardrails": [
        {"operation": r.operation, "is_blocked": r.is_blocked}
        for r in rules
    ]}

@router.put("/guardrails")
def update_guardrail(
    payload: GuardrailUpdate,
    db: Session = Depends(get_db)
):
    rule = db.query(Guardrail).filter_by(
        operation=payload.operation.upper()
    ).first()
    if not rule:
        rule = Guardrail(
            operation=payload.operation.upper(),
            is_blocked=payload.is_blocked
        )
        db.add(rule)
    else:
        rule.is_blocked = payload.is_blocked  # type: ignore[assignment]
    db.commit()
    return {
        "status": "updated",
        "operation": payload.operation.upper(),
        "is_blocked": payload.is_blocked,
    }