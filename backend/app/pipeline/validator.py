import sqlparse
import sqlglot
from app.core.config import get_settings
from app.models.schemas import ValidatorOutput

settings = get_settings()

BLOCKED_KEYWORDS = {
    "DROP","DELETE","UPDATE","INSERT",
    "TRUNCATE","ALTER","CREATE","REPLACE",
    "MERGE","EXEC","EXECUTE",
}

def validate_sql(sql: str) -> ValidatorOutput:
    errors  = []
    cleaned = sql.strip().rstrip(";")

    # 1. blocklist check
    tokens = [t.ttype for t in sqlparse.parse(cleaned)[0].flatten()]
    upper  = cleaned.upper()
    for kw in BLOCKED_KEYWORDS:
        if kw in upper.split():
            errors.append(f"Blocked keyword detected: {kw}")

    # 2. must be SELECT
    parsed = sqlparse.parse(cleaned)
    if not parsed or parsed[0].get_type() != "SELECT":
        errors.append("Only SELECT queries are allowed.")

    # 3. sqlglot syntax check
    try:
        sqlglot.parse_one(cleaned, dialect="mysql")
    except sqlglot.errors.ParseError as e:
        errors.append(f"Syntax error: {str(e)}")

    # 4. auto-add LIMIT if missing
    if "LIMIT" not in upper:
        cleaned = f"{cleaned} LIMIT {settings.max_rows_default}"

    if errors:
        return ValidatorOutput(
            valid=False,
            sanitized_sql=cleaned,
            errors=errors,
        )

    return ValidatorOutput(
        valid=True,
        sanitized_sql=cleaned,
        errors=[],
    )