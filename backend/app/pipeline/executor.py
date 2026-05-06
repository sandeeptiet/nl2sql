import time
from sqlalchemy import text
from app.core.database import readonly_engine
from app.models.schemas import ExecutorOutput

def execute_sql(sql: str) -> ExecutorOutput:
    start = time.perf_counter()

    try:
        with readonly_engine.connect() as conn:
            result  = conn.execute(text(sql))
            columns = list(result.keys())
            rows    = [dict(zip(columns, row)) for row in result.fetchall()]

        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        return ExecutorOutput(
            rows=rows,
            columns=columns,
            row_count=len(rows),
            latency_ms=latency_ms,
        )

    except Exception as e:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return ExecutorOutput(
            rows=[],
            columns=[],
            row_count=0,
            latency_ms=latency_ms,
            error=str(e),
        )