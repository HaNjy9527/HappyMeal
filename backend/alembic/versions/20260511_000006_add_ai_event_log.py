"""add ai_event_log table

Revision ID: 20260511_000006
Revises: 20260511_000005
Create Date: 2026-05-11 00:00:06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260511_000006"
down_revision: str | None = "20260511_000005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_event_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("analysis_id", sa.String(36), sa.ForeignKey("food_analyses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event", sa.String(50), nullable=False),
        sa.Column("outcome", sa.String(30), nullable=True),
        sa.Column("reason", sa.String(50), nullable=True),
        sa.Column("candidate_count", sa.Integer, nullable=True),
        sa.Column("item_count", sa.Integer, nullable=True),
        sa.Column("manual_review_required", sa.Boolean, nullable=True),
        sa.Column("has_instruction", sa.Boolean, nullable=True),
        sa.Column("used_fallback", sa.Boolean, nullable=True),
        sa.Column("input_tokens", sa.Integer, nullable=True),
        sa.Column("output_tokens", sa.Integer, nullable=True),
        sa.Column("prompt_version", sa.String(20), nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ai_event_log_created_at", "ai_event_log", ["created_at"])
    op.create_index("ix_ai_event_log_event_outcome", "ai_event_log", ["event", "outcome"])
    op.create_index("ix_ai_event_log_analysis_id", "ai_event_log", ["analysis_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_event_log_analysis_id", table_name="ai_event_log")
    op.drop_index("ix_ai_event_log_event_outcome", table_name="ai_event_log")
    op.drop_index("ix_ai_event_log_created_at", table_name="ai_event_log")
    op.drop_table("ai_event_log")
