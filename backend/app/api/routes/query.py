from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.schemas import QueryRequest, QueryResponse, QueryType
from app.models.db_models import QueryLog
from app.pipeline.classifier import classify_query
from app.pipeline.schema_linker import link_schema
from app.pipeline.retriever import retrieve_examples
from app.pipeline.generator import generate_sql
from app.pipeline.validator import validate_sql
from app.pipeline.executor import execute_sql
from app.pipeline.formatter import format_result

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def run_query(request: QueryRequest, db: Session = Depends(get_db)):

    # Step 1 — classify
    classifier_out = classify_query(request.question)

    # Step 2 — block unsupported
    if classifier_out.query_type == QueryType.UNSUPPORTED:
        return QueryResponse(
            nl_summary="Sorry, I can only answer data questions. "
                       "Modifications like INSERT, UPDATE or DELETE are not supported.",
            table=[], columns=[], sql="",
            query_type=QueryType.UNSUPPORTED,
            row_count=0, latency_ms=0,
        )

    # Step 3 — link schema
    linker_out = link_schema(
        request.question,
        classifier_out.tables_mentioned,
    )

    # Step 4 — retrieve examples
    retriever_out = retrieve_examples(request.question)

    # Step 5 — generate SQL
    generator_out = generate_sql(
        request.question,
        classifier_out,
        linker_out,
        retriever_out,
    )

    # Step 6 — validate
    validator_out = validate_sql(generator_out.sql)

    # Step 7 — execute (retry once if fails)
    executor_out = execute_sql(validator_out.sanitized_sql)
    if executor_out.error:
        # self-healing: retry with error context injected
        from app.pipeline.generator import llm, GENERATOR_PROMPT
        from langchain_core.messages import HumanMessage
        retry_prompt = (
            f"The following SQL failed with error: {executor_out.error}\n"
            f"Original SQL: {validator_out.sanitized_sql}\n"
            f"Please fix and return only the corrected SQL."
        )
        retry_response = llm.invoke([HumanMessage(content=retry_prompt)])
        retry_validator = validate_sql(str(retry_response.content).strip())
        executor_out    = execute_sql(retry_validator.sanitized_sql)

    # Step 8 — format
    formatter_out = format_result(request.question, executor_out)

    # Step 9 — log to DB
    log = QueryLog(
        nl_input    =request.question,
        generated_sql=validator_out.sanitized_sql,
        query_type  =classifier_out.query_type.value,
        status      ="error" if executor_out.error else "success",
        latency_ms  =executor_out.latency_ms,
        row_count   =executor_out.row_count,
        error_msg   =executor_out.error,
    )
    db.add(log)
    db.commit()

    return QueryResponse(
        nl_summary  =formatter_out.nl_summary,
        table       =formatter_out.table,
        columns     =formatter_out.columns,
        sql         =validator_out.sanitized_sql,
        query_type  =classifier_out.query_type.value,
        row_count   =executor_out.row_count,
        latency_ms  =executor_out.latency_ms,
        chart_type  =formatter_out.chart_type,
        error       =executor_out.error,
    )