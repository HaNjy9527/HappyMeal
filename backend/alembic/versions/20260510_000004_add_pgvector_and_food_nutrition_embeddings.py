"""add pgvector extension and food_nutrition_embeddings table

Revision ID: 20260510_000004
Revises: 20260501_000003
Create Date: 2026-05-10 00:00:04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260510_000004"
down_revision: str | None = "20260501_000003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "food_nutrition_embeddings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("canonical_food_name", sa.String(255), nullable=False),
        sa.Column("display_name_zh", sa.String(255), nullable=False),
        sa.Column("embed_text", sa.Text, nullable=False),
        sa.Column("embedding", sa.Text, nullable=True),
        sa.Column("kcal_per_100g", sa.Numeric(7, 2), nullable=False),
        sa.Column("protein_g_per_100g", sa.Numeric(7, 2), nullable=False),
        sa.Column("fat_g_per_100g", sa.Numeric(7, 2), nullable=False),
        sa.Column("carb_g_per_100g", sa.Numeric(7, 2), nullable=False),
        sa.Column("source", sa.String(50), nullable=False, server_default="official"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # extension 已啟用後，把 embedding 欄位改為真正的 vector(1536) 型別
    op.execute(
        "ALTER TABLE food_nutrition_embeddings "
        "ALTER COLUMN embedding TYPE vector(1536) USING NULL::vector(1536)"
    )

    op.create_index(
        "ix_food_nutrition_embeddings_canonical",
        "food_nutrition_embeddings",
        ["canonical_food_name"],
        unique=True,
    )

    # HNSW 索引：空表即可建立，不需要 training data
    op.execute(
        "CREATE INDEX ix_food_nutrition_embeddings_embedding "
        "ON food_nutrition_embeddings "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_food_nutrition_embeddings_embedding")
    op.drop_index("ix_food_nutrition_embeddings_canonical", table_name="food_nutrition_embeddings")
    op.drop_table("food_nutrition_embeddings")
    op.execute("DROP EXTENSION IF EXISTS vector")
