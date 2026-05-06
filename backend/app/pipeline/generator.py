from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import get_settings
from app.models.schemas import (
    GeneratorOutput, LinkerOutput,
    RetrieverOutput, ClassifierOutput
)

settings = get_settings()

llm = ChatAnthropic(
    model_name="claude-sonnet-4-6",
    api_key=settings.anthropic_api_key,
    temperature=0.0,
    max_tokens=1000,
)

GENERATOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert MySQL query writer for an e-commerce database.

RULES:
- Generate ONLY SELECT statements. Never use INSERT, UPDATE, DELETE, DROP, ALTER.
- Use only MySQL 8.0 syntax.
- Always add LIMIT 100 unless the user asks for a specific number.
- Use table aliases for readability.
- Return ONLY the SQL query on one line, then on a new line write: EXPLANATION: <one sentence>.

DATABASE SCHEMA:
{schema_context}

EXAMPLES:
{examples}
"""),
    ("human", "Question: {question}\nQuery type: {query_type}")
])

def generate_sql(
    question: str,
    classifier_output: ClassifierOutput,
    linker_output: LinkerOutput,
    retriever_output: RetrieverOutput,
) -> GeneratorOutput:

    # format few-shot examples
    examples_text = ""
    for ex in retriever_output.examples:
        examples_text += f"Q: {ex.question}\nSQL: {ex.sql}\n\n"

    if not examples_text:
        examples_text = "No examples available."

    response = llm.invoke(
        GENERATOR_PROMPT.format_messages(
            schema_context=linker_output.schema_context,
            examples=examples_text,
            question=question,
            query_type=classifier_output.query_type.value,
        )
    )

    raw = str(response.content).strip()

    # split SQL from explanation
    sql, explanation = raw, "No explanation provided."
    if "EXPLANATION:" in raw:
        parts       = raw.split("EXPLANATION:", 1)
        sql         = parts[0].strip()
        explanation = parts[1].strip()

    return GeneratorOutput(sql=sql, explanation=explanation)