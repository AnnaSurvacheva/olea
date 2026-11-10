"""add unique index on normalized email

Revision ID: f957ee07a099
Revises: 60d6992957c5
Create Date: 2026-10-13 13:14:54.562913

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f957ee07a099"
down_revision: str | Sequence[str] | None = "60d6992957c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE users SET email = lower(trim(email))")
    op.execute("CREATE UNIQUE INDEX ix_users_email_lower ON users (lower(email))")


def downgrade() -> None:
    op.execute("DROP INDEX ix_users_email_lower")
