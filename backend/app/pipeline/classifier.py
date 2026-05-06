from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.core.config import get_settings
from app.models.schemas import ClassifierOutput, QueryType

settings = get_settings()

llm = ChatAnthropic(
    model_name="claude-sonnet-4-6",
    api_key=settings.anthropic_api_key,
    temperature=0.0,
    max_tokens=300,
)

CLASSIFIER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a SQL query classifier for an e-commerce database.
Classify the user's question into exactly one of these types:
- SELECT_SIMPLE: basic lookup, no aggregation, no joins needed
- SELECT_AGGREGATE: uses SUM, COUNT, AVG, MAX, MIN or GROUP BY
- SELECT_JOIN: requires joining 2 or more tables
- SELECT_TEMPORAL: involves date/time filtering or arithmetic
- UNSUPPORTED: involves INSERT, UPDATE, DELETE, DROP or is not a data question

Also identify which tables and columns are mentioned or implied.

Tables available: customers, products, categories, orders, order_items, reviews

Respond with ONLY valid JSON in this exact format:
{{
  "query_type": "SELECT_AGGREGATE",
  "tables_mentioned": ["orders", "customers"],
  "columns_mentioned": ["total", "name"],
  "reason": "brief reason"
}}"""),
    ("human", "{question}")
])

parser = JsonOutputParser()
classifier_chain = CLASSIFIER_PROMPT | llm | parser

def classify_query(question: str) -> ClassifierOutput:
    result = classifier_chain.invoke({"question": question})
    return ClassifierOutput(**result)