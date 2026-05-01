"""add recommendation snapshot source

Revision ID: 20260501_000003
Revises: 20260425_000002
Create Date: 2026-05-01 00:00:03
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260501_000003"
down_revision: str | None = "20260425_000002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "recommendation_snapshots",
        sa.Column("source", sa.String(length=32), nullable=False, server_default="personalized"),
    )
    op.alter_column("recommendation_snapshots", "source", server_default=None)


def downgrade() -> None:
    op.drop_column("recommendation_snapshots", "source")