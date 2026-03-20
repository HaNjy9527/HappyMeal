"""init step2 core tables

Revision ID: 20260320_000001
Revises:
Create Date: 2026-03-20 00:00:01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260320_000001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("line_user_id", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column(
            "theme_preference",
            sa.Enum("female_default", "male_default", name="theme_preference", native_enum=False),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_line_user_id"), "users", ["line_user_id"], unique=True)

    op.create_table(
        "exercise_catalog",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("met_value", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("is_popular", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_exercise_catalog_name"),
    )
    op.create_index(op.f("ix_exercise_catalog_category"), "exercise_catalog", ["category"], unique=False)
    op.create_index(op.f("ix_exercise_catalog_display_order"), "exercise_catalog", ["display_order"], unique=False)
    op.create_index(op.f("ix_exercise_catalog_is_popular"), "exercise_catalog", ["is_popular"], unique=False)

    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("height_cm", sa.Integer(), nullable=True),
        sa.Column("weight_kg", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column(
            "activity_level",
            sa.Enum(
                "sedentary",
                "light",
                "moderate",
                "active",
                "very_active",
                name="activity_level",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "goal_type",
            sa.Enum("muscle_gain", "fat_loss", name="goal_type", native_enum=False),
            nullable=True,
        ),
        sa.Column("goal_weight_kg", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "food_analyses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "awaiting_confirmation", "completed", name="analysis_status", native_enum=False),
            nullable=False,
        ),
        sa.Column("total_kcal", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("total_protein_g", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("total_fat_g", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("total_carb_g", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_food_analyses_analyzed_at"), "food_analyses", ["analyzed_at"], unique=False)
    op.create_index(op.f("ix_food_analyses_status"), "food_analyses", ["status"], unique=False)
    op.create_index(op.f("ix_food_analyses_user_id"), "food_analyses", ["user_id"], unique=False)

    op.create_table(
        "consent_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column(
            "consent_type",
            sa.Enum("privacy_policy", "non_medical_disclosure", name="consent_type", native_enum=False),
            nullable=False,
        ),
        sa.Column("policy_version", sa.String(length=50), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "consent_type", "policy_version", name="uq_user_consent_version"),
    )
    op.create_index("ix_consent_records_user_accepted_at", "consent_records", ["user_id", "accepted_at"], unique=False)

    op.create_table(
        "food_analysis_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("food_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_food_name", sa.String(length=255), nullable=False),
        sa.Column("portion_value", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("portion_unit", sa.String(length=50), nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("kcal", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("protein_g", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("fat_g", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("carb_g", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["food_analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_food_analysis_items_analysis_id"), "food_analysis_items", ["analysis_id"], unique=False)

    op.create_table(
        "recommendation_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("target_calories_kcal", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("target_protein_g", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("target_fat_g", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("target_carb_g", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("recommended_exercises_json", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["food_analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("analysis_id"),
    )


def downgrade() -> None:
    op.drop_table("recommendation_snapshots")
    op.drop_index(op.f("ix_food_analysis_items_analysis_id"), table_name="food_analysis_items")
    op.drop_table("food_analysis_items")
    op.drop_index("ix_consent_records_user_accepted_at", table_name="consent_records")
    op.drop_table("consent_records")
    op.drop_index(op.f("ix_food_analyses_user_id"), table_name="food_analyses")
    op.drop_index(op.f("ix_food_analyses_status"), table_name="food_analyses")
    op.drop_index(op.f("ix_food_analyses_analyzed_at"), table_name="food_analyses")
    op.drop_table("food_analyses")
    op.drop_table("user_profiles")
    op.drop_index(op.f("ix_exercise_catalog_is_popular"), table_name="exercise_catalog")
    op.drop_index(op.f("ix_exercise_catalog_display_order"), table_name="exercise_catalog")
    op.drop_index(op.f("ix_exercise_catalog_category"), table_name="exercise_catalog")
    op.drop_table("exercise_catalog")
    op.drop_index(op.f("ix_users_line_user_id"), table_name="users")
    op.drop_table("users")