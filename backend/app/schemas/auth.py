from pydantic import BaseModel, ConfigDict

from app.db.models import ThemePreference


class AuthMeResponse(BaseModel):
    id: str
    display_name: str
    avatar_url: str | None
    theme_preference: ThemePreference

    model_config = ConfigDict(from_attributes=True)