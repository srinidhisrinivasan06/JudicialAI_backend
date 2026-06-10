from typing import Any, Dict, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "JusticeLens"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Security
    SECRET_KEY: str = "dev_secret_key_change_me_in_production_1234567890"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520  # 8 days

    # PostgreSQL Database
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "justicelens"
    POSTGRES_PORT: str = "5432"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: Any) -> Any:
        if isinstance(v, str) and v:
            return v
        data = info.data
        user = data.get("POSTGRES_USER")
        password = data.get("POSTGRES_PASSWORD")
        server = data.get("POSTGRES_SERVER")
        port = data.get("POSTGRES_PORT")
        db = data.get("POSTGRES_DB")
        return f"postgresql://{user}:{password}@{server}:{port}/{db}"

    # Gemini API Key
    GEMINI_API_KEY: Optional[str] = None

    # Configuration for loading files
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
