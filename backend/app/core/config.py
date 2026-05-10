"""
This is the core file that reads .env.local and makes all config available across the entire backend.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # Database
    db_host: str
    db_port: int = 3306
    db_user: str
    db_password: str
    db_name: str
    db_readonly_user: str
    db_readonly_password: str

    # Anthropic
    anthropic_api_key: str

    # FAISS
    faiss_index_path: str = "./data/faiss.index"

    # LangSmith (auto-picked up by LangChain)
    langchain_tracing_v2: str = "true"
    langchain_api_key: str = ""
    langchain_project: str = "nl2sql-local"

    # App
    app_env: str = "local"
    max_rows_default: int = 100

    @property
    def db_url(self) -> str:
        return (
            f"mysql+mysqlconnector://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def db_readonly_url(self) -> str:
        return (
            f"mysql+mysqlconnector://{self.db_readonly_user}:{self.db_readonly_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    class Config:
        env_file = ".env.local"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()