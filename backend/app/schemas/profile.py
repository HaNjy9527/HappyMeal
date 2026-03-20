from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import ActivityLevel, GoalType, ThemePreference


class UserProfilePayload(BaseModel):
    age: int | None = Field(default=None, ge=13, le=120)
    height_cm: int | None = Field(default=None, ge=100, le=250)
    weight_kg: Decimal | None = Field(default=None, ge=20, le=300)
    activity_level: ActivityLevel | None = None
    goal_type: GoalType | None = None
    goal_weight_kg: Decimal | None = Field(default=None, ge=20, le=300)
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ProfileResponse(BaseModel):
    user_id: str
    display_name: str
    avatar_url: str | None
    theme_preference: ThemePreference
    profile: UserProfilePayload


class ProfileUpdateRequest(BaseModel):
    age: int = Field(ge=13, le=120)
    height_cm: int = Field(ge=100, le=250)
    weight_kg: Decimal = Field(ge=20, le=300)
    activity_level: ActivityLevel
    goal_type: GoalType
    goal_weight_kg: Decimal | None = Field(default=None, ge=20, le=300)


class ThemePreferenceUpdateRequest(BaseModel):
    theme_preference: ThemePreference