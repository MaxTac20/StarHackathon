from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SESSION_STATUSES = ("Failed", "Paid", "Reversed", "Verified")
TRY_STATUSES = ("Failed", "InBank", "NoAttempt", "Paid", "Reversed", "Verified")
VERIFY_TYPES = ("Automated", "Manual")


class DatasetImport(Base):
    __tablename__ = "dataset_imports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_filename: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64), unique=True)
    source_size_bytes: Mapped[int] = mapped_column(BigInteger)
    source_row_count: Mapped[int] = mapped_column(BigInteger)
    session_count: Mapped[int] = mapped_column(BigInteger)
    try_count: Mapped[int] = mapped_column(BigInteger)
    transformation_version: Mapped[str] = mapped_column(String(32))
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("source_size_bytes >= 0", name="ck_dataset_imports_size_nonnegative"),
        CheckConstraint("source_row_count >= 0", name="ck_dataset_imports_rows_nonnegative"),
        CheckConstraint("session_count >= 0", name="ck_dataset_imports_sessions_nonnegative"),
        CheckConstraint("try_count >= 0", name="ck_dataset_imports_tries_nonnegative"),
    )


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    import_id: Mapped[int] = mapped_column(
        ForeignKey("dataset_imports.id", ondelete="RESTRICT"), index=True
    )
    merchant_key: Mapped[str] = mapped_column(Text, unique=True)

    terminals: Mapped[list[Terminal]] = relationship(back_populates="merchant")
    sessions: Mapped[list[PaymentSession]] = relationship(
        back_populates="merchant", overlaps="sessions,terminal"
    )


class MerchantCategory(Base):
    __tablename__ = "merchant_categories"

    category_id: Mapped[str] = mapped_column(Text, primary_key=True)
    import_id: Mapped[int] = mapped_column(ForeignKey("dataset_imports.id", ondelete="RESTRICT"))
    title_fa: Mapped[str] = mapped_column(Text)

    sessions: Mapped[list[PaymentSession]] = relationship(back_populates="category")


class Terminal(Base):
    __tablename__ = "terminals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    import_id: Mapped[int] = mapped_column(ForeignKey("dataset_imports.id", ondelete="RESTRICT"))
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("merchants.id", ondelete="RESTRICT"), index=True
    )
    terminal_key: Mapped[str] = mapped_column(Text)

    merchant: Mapped[Merchant] = relationship(back_populates="terminals")
    sessions: Mapped[list[PaymentSession]] = relationship(
        back_populates="terminal", overlaps="merchant,sessions"
    )

    __table_args__ = (
        UniqueConstraint("merchant_id", "terminal_key", name="uq_terminals_merchant_key"),
        UniqueConstraint("id", "merchant_id", name="uq_terminals_id_merchant"),
    )


class PaymentSession(Base):
    __tablename__ = "payment_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    import_id: Mapped[int] = mapped_column(ForeignKey("dataset_imports.id", ondelete="RESTRICT"))
    session_key: Mapped[str] = mapped_column(Text, unique=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id", ondelete="RESTRICT"))
    terminal_id: Mapped[int] = mapped_column(BigInteger)
    category_id: Mapped[str] = mapped_column(
        ForeignKey("merchant_categories.category_id", ondelete="RESTRICT")
    )
    amount: Mapped[int] = mapped_column(BigInteger)
    adjusted_fee: Mapped[int] = mapped_column(BigInteger)
    session_status: Mapped[str] = mapped_column(String(16))
    verify_type: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))

    merchant: Mapped[Merchant] = relationship(
        back_populates="sessions", overlaps="sessions,terminal"
    )
    terminal: Mapped[Terminal] = relationship(
        back_populates="sessions", overlaps="merchant,sessions"
    )
    category: Mapped[MerchantCategory] = relationship(back_populates="sessions")
    tries: Mapped[list[PaymentTry]] = relationship(
        back_populates="session", order_by="PaymentTry.try_seq"
    )

    __table_args__ = (
        UniqueConstraint("id", "merchant_id", name="uq_payment_sessions_id_merchant"),
        ForeignKeyConstraint(
            ["terminal_id", "merchant_id"],
            ["terminals.id", "terminals.merchant_id"],
            name="fk_payment_sessions_terminal_merchant",
            ondelete="RESTRICT",
        ),
        CheckConstraint("amount >= 0", name="ck_payment_sessions_amount_nonnegative"),
        CheckConstraint("adjusted_fee >= 0", name="ck_payment_sessions_fee_nonnegative"),
        CheckConstraint(
            "session_status IN ('Failed', 'Paid', 'Reversed', 'Verified')",
            name="ck_payment_sessions_status",
        ),
        CheckConstraint(
            "verify_type IN ('Automated', 'Manual')", name="ck_payment_sessions_verify_type"
        ),
        Index("ix_payment_sessions_merchant_created", "merchant_id", "created_at"),
        Index("ix_payment_sessions_category_merchant", "category_id", "merchant_id"),
        Index(
            "ix_payment_sessions_merchant_terminal_created",
            "merchant_id",
            "terminal_id",
            "created_at",
        ),
        Index(
            "ix_payment_sessions_merchant_status_created",
            "merchant_id",
            "session_status",
            "created_at",
        ),
    )


class PaymentTry(Base):
    __tablename__ = "payment_tries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(BigInteger)
    merchant_id: Mapped[int] = mapped_column(BigInteger)
    try_seq: Mapped[int] = mapped_column(SmallInteger)
    try_status: Mapped[str] = mapped_column(String(16))
    switch_response_code: Mapped[str | None] = mapped_column(Text)
    psp_code: Mapped[str | None] = mapped_column(Text)
    issuer_bank_code: Mapped[str | None] = mapped_column(Text)
    payer_card_key: Mapped[str | None] = mapped_column(Text)
    init_time_ms: Mapped[int | None] = mapped_column(Integer)
    verify_time_ms: Mapped[int | None] = mapped_column(Integer)
    try_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))

    session: Mapped[PaymentSession] = relationship(back_populates="tries")

    __table_args__ = (
        ForeignKeyConstraint(
            ["session_id", "merchant_id"],
            ["payment_sessions.id", "payment_sessions.merchant_id"],
            name="fk_payment_tries_session_merchant",
            ondelete="CASCADE",
        ),
        UniqueConstraint("session_id", "try_seq", name="uq_payment_tries_session_seq"),
        CheckConstraint("try_seq >= 0", name="ck_payment_tries_seq_nonnegative"),
        CheckConstraint(
            "try_status IN ('Failed', 'InBank', 'NoAttempt', 'Paid', 'Reversed', 'Verified')",
            name="ck_payment_tries_status",
        ),
        CheckConstraint(
            "init_time_ms IS NULL OR init_time_ms >= 0",
            name="ck_payment_tries_init_time_nonnegative",
        ),
        CheckConstraint(
            "verify_time_ms IS NULL OR verify_time_ms >= 0",
            name="ck_payment_tries_verify_time_nonnegative",
        ),
        Index("ix_payment_tries_merchant_created", "merchant_id", "try_created_at"),
        Index(
            "ix_payment_tries_merchant_status_created",
            "merchant_id",
            "try_status",
            "try_created_at",
        ),
        Index(
            "ix_payment_tries_merchant_psp_created",
            "merchant_id",
            "psp_code",
            "try_created_at",
        ),
        Index(
            "ix_payment_tries_merchant_issuer_created",
            "merchant_id",
            "issuer_bank_code",
            "try_created_at",
        ),
        Index(
            "ix_payment_tries_merchant_response_created",
            "merchant_id",
            "switch_response_code",
            "try_created_at",
        ),
    )
