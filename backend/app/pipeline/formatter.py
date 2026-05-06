from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import get_settings
from app.models.schemas import FormatterOutput, ExecutorOutput
from typing import List
import json

settings = get_settings()

llm = ChatAnthropic(
    model_name="claude-sonnet-4-6",
    api_key=settings.anthropic_api_key,
    temperature=0.3,
    max_tokens=200,
)

FORMATTER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a data analyst summarizing query results.
Write 1-2 sentences summarizing the key insight from the data.
Be specific — mention actual numbers, names, or dates from the results.
Do not mention SQL. Write as if talking to a business user."""),
    ("human", "Question: {question}\n\nResults (first 5 rows): {sample_rows}")
])

def detect_chart_type(columns: List[str], rows: list) -> str | None:
    """Detect if result is chartable — bar or line."""
    if len(columns) != 2 or len(rows) < 2:
        return None

    # check if second column is numeric
    try:
        float(str(rows[0][columns[1]]).replace(",",""))
        is_numeric = True
    except (ValueError, TypeError):
        is_numeric = False

    if not is_numeric:
        return None

    # if first column looks like a date → line chart
    first_val = str(rows[0][columns[0]]).lower()
    date_hints = ["jan","feb","mar","apr","may","jun",
                  "jul","aug","sep","oct","nov","dec",
                  "2022","2023","2024","2025","q1","q2","q3","q4"]
    if any(h in first_val for h in date_hints):
        return "line"

    return "bar"

def format_result(
    question: str,
    executor_output: ExecutorOutput,
) -> FormatterOutput:

    if executor_output.error:
        return FormatterOutput(
            table=[],
            columns=[],
            nl_summary=f"Query failed: {executor_output.error}",
            chart_type=None,
        )

    if not executor_output.rows:
        return FormatterOutput(
            table=[],
            columns=executor_output.columns,
            nl_summary="No results found for your question.",
            chart_type=None,
        )

    # sample first 5 rows for summary
    sample = executor_output.rows[:5]
    sample_text = json.dumps(sample, indent=2, default=str)

    response = llm.invoke(
        FORMATTER_PROMPT.format_messages(
            question=question,
            sample_rows=sample_text,
        )
    )

    chart_type = detect_chart_type(
        executor_output.columns,
        executor_output.rows
    )

    return FormatterOutput(
        table=executor_output.rows,
        columns=executor_output.columns,
        nl_summary=str(response.content).strip(),
        chart_type=chart_type,
    )