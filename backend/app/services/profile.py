from sqlalchemy.orm import Session

from app.db.models import User, UserProfile
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest, ThemePreferenceUpdateRequest, UserProfilePayload


def get_or_create_profile(db: Session, user: User) -> UserProfile:
    if user.profile is not None:
        return user.profile

    profile = UserProfile(user_id=user.id)
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user.profile


def build_profile_response(db: Session, user: User) -> ProfileResponse:
    profile = get_or_create_profile(db, user)
    return ProfileResponse(
        user_id=user.id,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        theme_preference=user.theme_preference,
        profile=UserProfilePayload.model_validate(profile),
    )


def update_profile(db: Session, user: User, payload: ProfileUpdateRequest) -> ProfileResponse:
    profile = get_or_create_profile(db, user)

    profile.age = payload.age
    profile.height_cm = payload.height_cm
    profile.weight_kg = payload.weight_kg
    profile.activity_level = payload.activity_level
    profile.goal_type = payload.goal_type
    profile.goal_weight_kg = payload.goal_weight_kg

    db.add(profile)
    db.commit()
    db.refresh(user)
    return build_profile_response(db, user)


def update_theme_preference(db: Session, user: User, payload: ThemePreferenceUpdateRequest) -> ProfileResponse:
    user.theme_preference = payload.theme_preference
    db.add(user)
    db.commit()
    db.refresh(user)
    return build_profile_response(db, user)