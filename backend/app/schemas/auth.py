from pydantic import BaseModel, ConfigDict

from app.db.models import ThemePreference


class ConsentStatusResponse(BaseModel):
    has_privacy_policy: bool
    has_non_medical_disclosure: bool
    can_start_analysis: bool
    can_view_guidance: bool


class RequiredPolicyVersionsResponse(BaseModel):
    privacy_policy: str
    non_medical_disclosure: str


class AuthMeResponse(BaseModel):
    id: str
    display_name: str
    avatar_url: str | None
    theme_preference: ThemePreference
    consent_status: ConsentStatusResponse
    required_policy_versions: RequiredPolicyVersionsResponse

    model_config = ConfigDict(from_attributes=True)