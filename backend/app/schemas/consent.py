from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import ConsentType


class ConsentCreateRequest(BaseModel):
    consent_type: ConsentType
    policy_version: str = Field(min_length=1, max_length=50)


class ConsentRecordResponse(BaseModel):
    id: str
    consent_type: ConsentType
    policy_version: str
    accepted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CurrentConsentsResponse(BaseModel):
    items: list[ConsentRecordResponse]