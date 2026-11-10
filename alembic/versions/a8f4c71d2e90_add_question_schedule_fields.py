"""add question creation and schedule fields

Revision ID: a8f4c71d2e90
Revises: f957ee07a099
Create Date: 2026-11-10

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a8f4c71d2e90"
down_revision: str | Sequence[str] | None = "f957ee07a099"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "questions",
        sa.Column("for_day", sa.Date(), nullable=True),
    )
    op.execute(
        """
        WITH numbered_questions AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY id) - 1 AS day_offset
            FROM questions
        )
        UPDATE questions
        SET for_day = DATE '2026-11-10' + numbered_questions.day_offset::integer
        FROM numbered_questions
        WHERE questions.id = numbered_questions.id
        """
    )
    op.alter_column(
        "questions",
        "for_day",
        existing_type=sa.Date(),
        nullable=False,
    )
    op.create_unique_constraint(
        "uq_questions_for_day",
        "questions",
        ["for_day"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_questions_for_day", "questions", type_="unique")
    op.drop_column("questions", "for_day")
    op.drop_column("questions", "created_at")
