# backend/app/core/init_db.py
from app.core.database import engine, Base
from app.models.db_models import (
    QueryLog, FewShotExample,
    SchemaMetadata, Guardrail, ModelConfig
)

def init_db():
    Base.metadata.create_all(bind=engine)
    print("All admin tables created.")

if __name__ == "__main__":
    init_db()