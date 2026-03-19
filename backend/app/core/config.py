from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="HappyMeal API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    database_url: str = Field(
        default="postgresql+psycopg://happymeal:happymeal@db:5432/happymeal",
        alias="DATABASE_URL",
    )
    line_channel_id: str = Field(default="", alias="LINE_CHANNEL_ID")
    line_channel_secret: str = Field(default="", alias="LINE_CHANNEL_SECRET")
    line_redirect_uri: str = Field(default="", alias="LINE_REDIRECT_URI")
    ai_food_api_key: str = Field(default="", alias="AI_FOOD_API_KEY")
    nutrition_data_source: str = Field(default="", alias="NUTRITION_DATA_SOURCE")

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
