from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.db_models import FewShotExample
from app.pipeline.retriever import build_faiss_index
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ExampleCreate(BaseModel):
    question: str
    sql: str
    query_type: Optional[str] = None

class ExampleUpdate(BaseModel):
    question: Optional[str] = None
    sql: Optional[str] = None
    query_type: Optional[str] = None

@router.get("/examples")
def list_examples(
    search: Optional[str] = None,
    query_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(FewShotExample)
    if search:
        q = q.filter(FewShotExample.question.ilike(f"%{search}%"))
    if query_type:
        q = q.filter(FewShotExample.query_type == query_type)
    examples = q.order_by(FewShotExample.created_at.desc()).all()
    return {"examples": [
        {
            "id":         e.id,
            "question":   e.question,
            "sql":        e.sql,
            "query_type": e.query_type,
            "created_at": str(e.created_at),
        }
        for e in examples
    ]}

@router.post("/examples")
def add_example(
    payload: ExampleCreate,
    db: Session = Depends(get_db)
):
    example = FewShotExample(
        question=payload.question,
        sql=payload.sql,
        query_type=payload.query_type,
    )
    db.add(example)
    db.commit()
    db.refresh(example)
    # rebuild FAISS index with new example
    build_faiss_index()
    return {"status": "created", "id": example.id}

@router.put("/examples/{example_id}")
def update_example(
    example_id: int,
    payload: ExampleUpdate,
    db: Session = Depends(get_db)
):
    example = db.query(FewShotExample).filter_by(id=example_id).first()
    if not example:
        raise HTTPException(status_code=404, detail="Example not found")
    if payload.question:
        example.question = payload.question      # type: ignore[assignment]
    if payload.sql:
        example.sql = payload.sql                # type: ignore[assignment]
    if payload.query_type:
        example.query_type = payload.query_type  # type: ignore[assignment]
    db.commit()
    # rebuild FAISS index with updated example
    build_faiss_index()
    return {"status": "updated", "id": example_id}

@router.delete("/examples/{example_id}")
def delete_example(
    example_id: int,
    db: Session = Depends(get_db)
):
    example = db.query(FewShotExample).filter_by(id=example_id).first()
    if not example:
        raise HTTPException(status_code=404, detail="Example not found")
    db.delete(example)
    db.commit()
    # rebuild FAISS index without deleted example
    build_faiss_index()
    return {"status": "deleted", "id": example_id}