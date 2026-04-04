from pathlib import Path
from functools import lru_cache
from urllib.parse import urlsplit, urlunsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="HappyMeal API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    cors_allow_origins: list[str] | str = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ],
        alias="CORS_ALLOW_ORIGINS",
    )

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> object:
        if isinstance(v, str):
            value = v.strip()
            if not value:
                return []
            if not value.startswith("["):
                return [origin.strip() for origin in value.split(",") if origin.strip()]
        return v
    analysis_upload_dir: str = Field(default="tmp/analysis-uploads", alias="ANALYSIS_UPLOAD_DIR")
    analysis_max_upload_bytes: int = Field(default=5_000_000, alias="ANALYSIS_MAX_UPLOAD_BYTES")
    database_url: str = Field(
        default="postgresql+psycopg://happymeal:happymeal@db:5432/happymeal",
        alias="DATABASE_URL",
    )
    line_channel_id: str = Field(default="", alias="LINE_CHANNEL_ID")
    line_channel_secret: str = Field(default="", alias="LINE_CHANNEL_SECRET")
    line_callback_url: str = Field(default="", alias="LINE_CALLBACK_URL")
    session_secret_key: str = Field(default="", alias="SESSION_SECRET_KEY")
    frontend_url: str = Field(default="", alias="FRONTEND_URL")
    ai_food_api_key: str = Field(default="", alias="AI_API_KEY")
    nutrition_data_source: str = Field(default="", alias="NUTRITION_DATA_SOURCE")

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    @property
    def normalized_database_url(self) -> str:
        database_url = self.database_url

        if database_url.startswith("postgresql+"):
            return database_url

        if not database_url.startswith("postgresql://"):
            return database_url

        url_parts = urlsplit(database_url)
        return urlunsplit(("postgresql+psycopg", url_parts.netloc, url_parts.path, url_parts.query, url_parts.fragment))

    @property
    def analysis_upload_path(self) -> Path:
        return Path(self.analysis_upload_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()
