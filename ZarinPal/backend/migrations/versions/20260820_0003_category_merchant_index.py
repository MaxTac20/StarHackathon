"""Index payment sessions for merchant-category filtering.

Revision ID: 20260820_0003
Revises: 20260820_0002
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260820_0003"
down_revision: str | Sequence[str] | None = "20260820_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_payment_sessions_category_merchant",
        "payment_sessions",
        ["category_id", "merchant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_payment_sessions_category_merchant",
        table_name="payment_sessions",
    )
