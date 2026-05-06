from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.db_models import QueryLog
from typing import Optional
import csv
import io

router = APIRouter()

@router.get("/logs")
def get_logs(
    status:     Optional[str] = None,
    query_type: Optional[str] = None,
    limit:      int = 100,
    offset:     int = 0,
    db: Session = Depends(get_db)
):
    q = db.query(QueryLog)
    if status:
        q = q.filter(QueryLog.status == status)
    if query_type:
        q = q.filter(QueryLog.query_type == query_type)

    total = q.count()
    logs  = q.order_by(QueryLog.created_at.desc()) \
              .offset(offset).limit(limit).all()

    return {
        "total": total,
        "logs": [
            {
                "id":            l.id,
                "nl_input":      l.nl_input,
                "generated_sql": l.generated_sql,
                "query_type":    l.query_type,
                "status":        l.status,
                "latency_ms":    l.latency_ms,
                "row_count":     l.row_count,
                "error_msg":     l.error_msg,
                "created_at":    str(l.created_at),
            }
            for l in logs
        ],
    }

@router.get("/logs/export")
def export_logs_csv(db: Session = Depends(get_db)):
    logs = db.query(QueryLog).order_by(QueryLog.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id","nl_input","generated_sql","query_type",
        "status","latency_ms","row_count","error_msg","created_at"
    ])
    for l in logs:
        writer.writerow([
            l.id, l.nl_input, l.generated_sql, l.query_type,
            l.status, l.latency_ms, l.row_count,
            l.error_msg, l.created_at
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=query_logs.csv"}
    )