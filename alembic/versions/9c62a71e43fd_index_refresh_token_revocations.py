"""index refresh-token revocations for retention cleanup

Revision ID: 9c62a71e43fd
Revises: bd43c2b9f102
Create Date: 2026-11-12

"""

from collections.abc import Sequence

from alembic import op

revision: str = "9c62a71e43fd"
down_revision: str | Sequence[str] | None = "bd43c2b9f102"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add an index used to find old revoked refresh-token rows."""
    op.create_index(
        "ix_refresh_tokens_revoked_at",
        "refresh_tokens",
        ["revoked_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the refresh-token revocation timestamp index."""
    op.drop_index("ix_refresh_tokens_revoked_at", table_name="refresh_tokens")
