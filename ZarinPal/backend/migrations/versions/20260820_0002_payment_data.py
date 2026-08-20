"""Add normalized payment dataset tables.

Revision ID: 20260820_0002
Revises: 20260819_0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0002"
down_revision: str | Sequence[str] | None = "20260819_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dataset_imports",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_filename", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("source_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("source_row_count", sa.BigInteger(), nullable=False),
        sa.Column("session_count", sa.BigInteger(), nullable=False),
        sa.Column("try_count", sa.BigInteger(), nullable=False),
        sa.Column("transformation_version", sa.String(length=32), nullable=False),
        sa.Column(
            "imported_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("session_count >= 0", name="ck_dataset_imports_sessions_nonnegative"),
        sa.CheckConstraint("source_row_count >= 0", name="ck_dataset_imports_rows_nonnegative"),
        sa.CheckConstraint("source_size_bytes >= 0", name="ck_dataset_imports_size_nonnegative"),
        sa.CheckConstraint("try_count >= 0", name="ck_dataset_imports_tries_nonnegative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sha256"),
    )
    op.create_table(
        "merchant_categories",
        sa.Column("category_id", sa.Text(), nullable=False),
        sa.Column("import_id", sa.BigInteger(), nullable=False),
        sa.Column("title_fa", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["import_id"], ["dataset_imports.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("category_id"),
    )
    op.create_table(
        "merchants",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("import_id", sa.BigInteger(), nullable=False),
        sa.Column("merchant_key", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["import_id"], ["dataset_imports.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_key"),
    )
    op.create_index(op.f("ix_merchants_import_id"), "merchants", ["import_id"], unique=False)
    op.create_table(
        "terminals",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("import_id", sa.BigInteger(), nullable=False),
        sa.Column("merchant_id", sa.BigInteger(), nullable=False),
        sa.Column("terminal_key", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["import_id"], ["dataset_imports.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "merchant_id", name="uq_terminals_id_merchant"),
        sa.UniqueConstraint("merchant_id", "terminal_key", name="uq_terminals_merchant_key"),
    )
    op.create_index(op.f("ix_terminals_merchant_id"), "terminals", ["merchant_id"], unique=False)
    op.create_table(
        "payment_sessions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("import_id", sa.BigInteger(), nullable=False),
        sa.Column("session_key", sa.Text(), nullable=False),
        sa.Column("merchant_id", sa.BigInteger(), nullable=False),
        sa.Column("terminal_id", sa.BigInteger(), nullable=False),
        sa.Column("category_id", sa.Text(), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("adjusted_fee", sa.BigInteger(), nullable=False),
        sa.Column("session_status", sa.String(length=16), nullable=False),
        sa.Column("verify_type", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("adjusted_fee >= 0", name="ck_payment_sessions_fee_nonnegative"),
        sa.CheckConstraint("amount >= 0", name="ck_payment_sessions_amount_nonnegative"),
        sa.CheckConstraint(
            "session_status IN ('Failed', 'Paid', 'Reversed', 'Verified')",
            name="ck_payment_sessions_status",
        ),
        sa.CheckConstraint(
            "verify_type IN ('Automated', 'Manual')", name="ck_payment_sessions_verify_type"
        ),
        sa.ForeignKeyConstraint(
            ["terminal_id", "merchant_id"],
            ["terminals.id", "terminals.merchant_id"],
            name="fk_payment_sessions_terminal_merchant",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"], ["merchant_categories.category_id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["import_id"], ["dataset_imports.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "merchant_id", name="uq_payment_sessions_id_merchant"),
        sa.UniqueConstraint("session_key"),
    )
    op.create_index(
        "ix_payment_sessions_merchant_created",
        "payment_sessions",
        ["merchant_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_payment_sessions_merchant_status_created",
        "payment_sessions",
        ["merchant_id", "session_status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_payment_sessions_merchant_terminal_created",
        "payment_sessions",
        ["merchant_id", "terminal_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "payment_tries",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.BigInteger(), nullable=False),
        sa.Column("merchant_id", sa.BigInteger(), nullable=False),
        sa.Column("try_seq", sa.SmallInteger(), nullable=False),
        sa.Column("try_status", sa.String(length=16), nullable=False),
        sa.Column("switch_response_code", sa.Text(), nullable=True),
        sa.Column("psp_code", sa.Text(), nullable=True),
        sa.Column("issuer_bank_code", sa.Text(), nullable=True),
        sa.Column("payer_card_key", sa.Text(), nullable=True),
        sa.Column("init_time_ms", sa.Integer(), nullable=True),
        sa.Column("verify_time_ms", sa.Integer(), nullable=True),
        sa.Column("try_created_at", sa.DateTime(), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("settled_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "init_time_ms IS NULL OR init_time_ms >= 0",
            name="ck_payment_tries_init_time_nonnegative",
        ),
        sa.CheckConstraint("try_seq >= 0", name="ck_payment_tries_seq_nonnegative"),
        sa.CheckConstraint(
            "try_status IN ('Failed', 'InBank', 'NoAttempt', 'Paid', 'Reversed', 'Verified')",
            name="ck_payment_tries_status",
        ),
        sa.CheckConstraint(
            "verify_time_ms IS NULL OR verify_time_ms >= 0",
            name="ck_payment_tries_verify_time_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["session_id", "merchant_id"],
            ["payment_sessions.id", "payment_sessions.merchant_id"],
            name="fk_payment_tries_session_merchant",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "try_seq", name="uq_payment_tries_session_seq"),
    )
    op.create_index(
        "ix_payment_tries_merchant_created",
        "payment_tries",
        ["merchant_id", "try_created_at"],
        unique=False,
    )
    op.create_index(
        "ix_payment_tries_merchant_issuer_created",
        "payment_tries",
        ["merchant_id", "issuer_bank_code", "try_created_at"],
        unique=False,
    )
    op.create_index(
        "ix_payment_tries_merchant_psp_created",
        "payment_tries",
        ["merchant_id", "psp_code", "try_created_at"],
        unique=False,
    )
    op.create_index(
        "ix_payment_tries_merchant_response_created",
        "payment_tries",
        ["merchant_id", "switch_response_code", "try_created_at"],
        unique=False,
    )
    op.create_index(
        "ix_payment_tries_merchant_status_created",
        "payment_tries",
        ["merchant_id", "try_status", "try_created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("payment_tries")
    op.drop_table("payment_sessions")
    op.drop_table("terminals")
    op.drop_table("merchants")
    op.drop_table("merchant_categories")
    op.drop_table("dataset_imports")
