from sqlalchemy import inspect, text
from app.core.database import engine
from app.models.schemas import LinkerOutput, SchemaTable, SchemaColumn
from app.models.db_models import SchemaMetadata
from app.core.database import SessionLocal
from typing import List

# synonym map — NL words → actual column names
SYNONYMS = {
    "revenue":   "orders.total",
    "sales":     "orders.total",
    "income":    "orders.total",
    "earnings":  "order_items.subtotal",
    "profit":    "order_items.subtotal",
    "buyer":     "customers.name",
    "client":    "customers.name",
    "user":      "customers.name",
    "item":      "products.name",
    "product":   "products.name",
    "rating":    "reviews.rating",
    "score":     "reviews.rating",
    "feedback":  "reviews.comment",
    "date":      "orders.created_at",
    "ordered":   "orders.created_at",
}

def get_full_schema() -> List[SchemaTable]:
    """Read live schema from MySQL via SQLAlchemy inspect."""
    inspector = inspect(engine)
    db = SessionLocal()
    tables = []

    try:
        for table_name in inspector.get_table_names():
            # skip admin tables
            if table_name in (
                "query_logs","few_shot_examples",
                "schema_metadata","guardrails","model_config"
            ):
                continue

            columns = []
            for col in inspector.get_columns(table_name):
                # fetch description from schema_metadata if exists
                meta = db.query(SchemaMetadata).filter_by(
                    table_name=table_name,
                    column_name=col["name"]
                ).first()

                columns.append(SchemaColumn(
                    name=col["name"],
                    type=str(col["type"]),
                    description=str(meta.description) if (meta and meta.description) else None,
                    is_sensitive=bool(meta.is_sensitive) if meta else False,
                ))

            tables.append(SchemaTable(
                name=table_name,
                columns=[c for c in columns if not c.is_sensitive]
            ))
    finally:
        db.close()

    return tables

def build_schema_context(tables: List[SchemaTable]) -> str:
    """Format schema as a readable string for the LLM prompt."""
    lines = []
    for table in tables:
        col_defs = []
        for col in table.columns:
            desc = f" -- {col.description}" if col.description else ""
            col_defs.append(f"  {col.name} {col.type}{desc}")
        lines.append(f"Table: {table.name}\n" + "\n".join(col_defs))
    return "\n\n".join(lines)

def link_schema(question: str, tables_mentioned: List[str]) -> LinkerOutput:
    """Map NL entities to actual schema columns, detect ambiguities."""
    all_tables  = get_full_schema()
    q_lower     = question.lower()
    ambiguities = []
    resolved_cols = []

    # check synonyms for ambiguities
    matched_synonyms = []
    for word, mapping in SYNONYMS.items():
        if word in q_lower:
            matched_synonyms.append((word, mapping))

    # flag ambiguous terms (revenue can mean two things)
    ambiguous_terms = {
        "revenue": ["orders.total", "order_items.subtotal"],
        "sales":   ["orders.total", "order_items.subtotal"],
    }
    for word, options in ambiguous_terms.items():
        if word in q_lower:
            ambiguities.append(
                f"'{word}' could refer to: {' or '.join(options)}"
            )

    for word, mapping in matched_synonyms:
        resolved_cols.append(mapping)

    schema_context = build_schema_context(all_tables)

    return LinkerOutput(
        resolved_tables=tables_mentioned,
        resolved_columns=resolved_cols,
        ambiguities=ambiguities,
        schema_context=schema_context,
    )