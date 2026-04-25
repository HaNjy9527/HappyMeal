"""add analysis item resolution metadata

Revision ID: 20260425_000002
Revises: 20260320_000001
Create Date: 2026-04-25 00:00:02
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260425_000002"
down_revision: str | None = "20260320_000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("food_analysis_items", sa.Column("source_portion_unit", sa.String(length=50), nullable=True))
    op.add_column("food_analysis_items", sa.Column("canonical_food_name", sa.String(length=255), nullable=True))
    op.add_column("food_analysis_items", sa.Column("nutrition_source", sa.String(length=50), nullable=True))
    op.add_column(
        "food_analysis_items",
        sa.Column("is_estimated", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("food_analysis_items", sa.Column("resolved_weight_g", sa.Numeric(precision=8, scale=2), nullable=True))
    op.add_column("food_analysis_items", sa.Column("weight_estimation_method", sa.String(length=50), nullable=True))
    op.alter_column("food_analysis_items", "is_estimated", server_default=None)


def downgrade() -> None:
    op.drop_column("food_analysis_items", "weight_estimation_method")
    op.drop_column("food_analysis_items", "resolved_weight_g")
    op.drop_column("food_analysis_items", "is_estimated")
    op.drop_column("food_analysis_items", "nutrition_source")
    op.drop_column("food_analysis_items", "canonical_food_name")
    op.drop_column("food_analysis_items", "source_portion_unit")