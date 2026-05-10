"""add food_code, food_category, nutrients_json to food_nutrition_embeddings

Revision ID: 20260511_000005
Revises: 20260510_000004
Create Date: 2026-05-11 00:00:05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260511_000005"
down_revision: str | None = "20260510_000004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("food_nutrition_embeddings", sa.Column("food_code", sa.String(20), nullable=True))
    op.add_column("food_nutrition_embeddings", sa.Column("food_category", sa.String(100), nullable=True))
    op.add_column("food_nutrition_embeddings", sa.Column("nutrients_json", postgresql.JSONB, nullable=True))

    op.create_index(
        "ix_food_nutrition_embeddings_food_code",
        "food_nutrition_embeddings",
        ["food_code"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_food_nutrition_embeddings_food_code", table_name="food_nutrition_embeddings")
    op.drop_column("food_nutrition_embeddings", "nutrients_json")
    op.drop_column("food_nutrition_embeddings", "food_category")
    op.drop_column("food_nutrition_embeddings", "food_code")
