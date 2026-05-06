from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from app.core.database import get_db, engine
from app.models.db_models import SchemaMetadata
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

class ColumnMetaUpdate(BaseModel):
    table_name: str
    column_name: str
    description: Optional[str] = None
    is_sensitive: bool = False

@router.get("/schema")
def get_schema(db: Session = Depends(get_db)):
    inspector = inspect(engine)
    admin_tables = {
        "query_logs", "few_shot_examples",
        "schema_metadata", "guardrails", "model_config"
    }
    result = []
    for table_name in inspector.get_table_names():
        if table_name in admin_tables:
            continue
        columns = []
        for col in inspector.get_columns(table_name):
            meta = db.query(SchemaMetadata).filter_by(
                table_name=table_name,
                column_name=col["name"]
            ).first()
            columns.append({
                "name":         col["name"],
                "type":         str(col["type"]),
                "description":  meta.description if meta else None,
                "is_sensitive": meta.is_sensitive if meta else False,
            })
        fks = inspector.get_foreign_keys(table_name)
        result.append({
            "table":        table_name,
            "columns":      columns,
            "foreign_keys": fks,
        })
    return {"tables": result}

@router.put("/schema/column")
def update_column_meta(
    payload: ColumnMetaUpdate,
    db: Session = Depends(get_db)
):
    meta = db.query(SchemaMetadata).filter_by(
        table_name=payload.table_name,
        column_name=payload.column_name,
    ).first()

    if meta:
        meta.description  = payload.description   # type: ignore[assignment]
        meta.is_sensitive = payload.is_sensitive  # type: ignore[assignment]
    else:
        meta = SchemaMetadata(
            table_name=payload.table_name,
            column_name=payload.column_name,
            description=payload.description,
            is_sensitive=payload.is_sensitive,
        )
        db.add(meta)

    db.commit()
    return {"status": "updated", "column": payload.column_name}