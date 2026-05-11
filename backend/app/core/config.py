from functools import lru_cache
from pathlib import Path
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
    session_cookie_name: str = Field(default="happymeal_session", alias="SESSION_COOKIE_NAME")
    session_cookie_domain: str | None = Field(default=None, alias="SESSION_COOKIE_DOMAIN")
    session_cookie_same_site: str | None = Field(default=None, alias="SESSION_COOKIE_SAME_SITE")
    session_cookie_https_only: bool | None = Field(default=None, alias="SESSION_COOKIE_HTTPS_ONLY")
    session_cookie_max_age: int = Field(default=60 * 60 * 24 * 7, alias="SESSION_COOKIE_MAX_AGE")
    frontend_url: str = Field(default="", alias="FRONTEND_URL")
    ai_food_api_key: str = Field(default="", alias="AI_API_KEY")
    ai_food_model: str = Field(default="gpt-5.4-mini", alias="AI_FOOD_MODEL")
    nutrition_data_source: str = Field(default="", alias="NUTRITION_DATA_SOURCE")
    image_preprocess_enabled: bool = Field(default=True, alias="IMAGE_PREPROCESS_ENABLED")
    image_preprocess_max_px: int = Field(default=1024, alias="IMAGE_PREPROCESS_MAX_PX")

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

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

    @field_validator("session_cookie_domain", mode="before")
    @classmethod
    def normalize_cookie_domain(cls, v: object) -> object:
        if isinstance(v, str):
            value = v.strip()
            return value or None
        return v

    @field_validator("session_cookie_same_site", mode="before")
    @classmethod
    def normalize_same_site(cls, v: object) -> object:
        if isinstance(v, str):
            value = v.strip().lower()
            return value or None
        return v

    @field_validator("session_cookie_https_only", mode="before")
    @classmethod
    def normalize_https_only(cls, v: object) -> object:
        if isinstance(v, str):
            value = v.strip().lower()
            return value or None
        return v

    @field_validator("session_cookie_same_site")
    @classmethod
    def validate_same_site(cls, v: str | None) -> str | None:
        if v is None:
            return v

        if v not in {"lax", "strict", "none"}:
            raise ValueError("SESSION_COOKIE_SAME_SITE must be one of: lax, strict, none")

        return v

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

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def effective_session_cookie_same_site(self) -> str:
        if self.session_cookie_same_site:
            return self.session_cookie_same_site

        return "none" if self.is_production else "lax"

    @property
    def effective_session_cookie_https_only(self) -> bool:
        if self.session_cookie_https_only is not None:
            return self.session_cookie_https_only

        return self.is_production


@lru_cache
def get_settings() -> Settings:
    return Settings()
