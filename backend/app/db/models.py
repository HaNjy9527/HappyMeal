from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, Enum as SqlEnum, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def generate_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AnalysisStatus(str, Enum):
    DRAFT = "draft"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    COMPLETED = "completed"


class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


class GoalType(str, Enum):
    MUSCLE_GAIN = "muscle_gain"
    FAT_LOSS = "fat_loss"


class ThemePreference(str, Enum):
    FEMALE_DEFAULT = "female_default"
    MALE_DEFAULT = "male_default"


class ConsentType(str, Enum):
    PRIVACY_POLICY = "privacy_policy"
    NON_MEDICAL_DISCLOSURE = "non_medical_disclosure"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    line_user_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    theme_preference: Mapped[ThemePreference] = mapped_column(
        SqlEnum(ThemePreference, name="theme_preference", native_enum=False),
        default=ThemePreference.FEMALE_DEFAULT,
        nullable=False,
    )

    profile: Mapped[UserProfile | None] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    analyses: Mapped[list[FoodAnalysis]] = relationship(back_populates="user", cascade="all, delete-orphan")
    consents: Mapped[list[ConsentRecord]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    age: Mapped[int | None] = mapped_column(nullable=True)
    height_cm: Mapped[int | None] = mapped_column(nullable=True)
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    activity_level: Mapped[ActivityLevel | None] = mapped_column(
        SqlEnum(ActivityLevel, name="activity_level", native_enum=False),
        nullable=True,
    )
    goal_type: Mapped[GoalType | None] = mapped_column(
        SqlEnum(GoalType, name="goal_type", native_enum=False),
        nullable=True,
    )
    goal_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user: Mapped[User] = relationship(back_populates="profile")


class FoodAnalysis(TimestampMixin, Base):
    __tablename__ = "food_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    status: Mapped[AnalysisStatus] = mapped_column(
        SqlEnum(AnalysisStatus, name="analysis_status", native_enum=False),
        default=AnalysisStatus.DRAFT,
        nullable=False,
        index=True,
    )
    total_kcal: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    total_protein_g: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    total_fat_g: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    total_carb_g: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)

    user: Mapped[User] = relationship(back_populates="analyses")
    items: Mapped[list[FoodAnalysisItem]] = relationship(back_populates="analysis", cascade="all, delete-orphan")
    recommendation_snapshot: Mapped[RecommendationSnapshot | None] = relationship(
        back_populates="analysis",
        uselist=False,
        cascade="all, delete-orphan",
    )


class FoodAnalysisItem(Base):
    __tablename__ = "food_analysis_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    analysis_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("food_analyses.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    food_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_food_name: Mapped[str] = mapped_column(String(255), nullable=False)
    portion_value: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    portion_unit: Mapped[str] = mapped_column(String(50), nullable=False)
    source_portion_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    canonical_food_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nutrition_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_estimated: Mapped[bool] = mapped_column(default=False, nullable=False)
    resolved_weight_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    weight_estimation_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    kcal: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    protein_g: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    fat_g: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    carb_g: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)

    analysis: Mapped[FoodAnalysis] = relationship(back_populates="items")


class RecommendationSnapshot(Base):
    __tablename__ = "recommendation_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    analysis_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("food_analyses.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="personalized")
    target_calories_kcal: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    target_protein_g: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    target_fat_g: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    target_carb_g: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    recommended_exercises_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    analysis: Mapped[FoodAnalysis] = relationship(back_populates="recommendation_snapshot")


class ExerciseCatalog(TimestampMixin, Base):
    __tablename__ = "exercise_catalog"
    __table_args__ = (UniqueConstraint("name", name="uq_exercise_catalog_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    met_value: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    display_order: Mapped[int] = mapped_column(nullable=False, index=True)
    is_popular: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)


class ConsentRecord(Base):
    __tablename__ = "consent_records"
    __table_args__ = (
        UniqueConstraint("user_id", "consent_type", "policy_version", name="uq_user_consent_version"),
        Index("ix_consent_records_user_accepted_at", "user_id", "accepted_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    consent_type: Mapped[ConsentType] = mapped_column(
        SqlEnum(ConsentType, name="consent_type", native_enum=False),
        nullable=False,
    )
    policy_version: Mapped[str] = mapped_column(String(50), nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user: Mapped[User] = relationship(back_populates="consents")


class FoodNutritionEmbedding(TimestampMixin, Base):
    __tablename__ = "food_nutrition_embeddings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    canonical_food_name: Mapped[str] = mapped_column(String(255), nullable=False)
    food_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    food_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    display_name_zh: Mapped[str] = mapped_column(String(255), nullable=False)
    embed_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    kcal_per_100g: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    protein_g_per_100g: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    fat_g_per_100g: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    carb_g_per_100g: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="official")
    nutrients_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AnalysisEventLog(Base):
    __tablename__ = "ai_event_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    analysis_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("food_analyses.id", ondelete="SET NULL"), nullable=True)
    event: Mapped[str] = mapped_column(String(50), nullable=False)
    outcome: Mapped[str | None] = mapped_column(String(30), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    candidate_count: Mapped[int | None] = mapped_column(nullable=True)
    item_count: Mapped[int | None] = mapped_column(nullable=True)
    manual_review_required: Mapped[bool | None] = mapped_column(nullable=True)
    has_instruction: Mapped[bool | None] = mapped_column(nullable=True)
    used_fallback: Mapped[bool | None] = mapped_column(nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)