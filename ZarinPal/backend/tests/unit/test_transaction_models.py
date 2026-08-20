from sqlalchemy import BigInteger, DateTime
from sqlalchemy.orm import configure_mappers

from app.db.base import Base


def test_payment_dataset_metadata_is_registered() -> None:
    configure_mappers()

    assert set(Base.metadata.tables) >= {
        "dataset_imports",
        "merchants",
        "merchant_categories",
        "terminals",
        "payment_sessions",
        "payment_tries",
    }


def test_source_timestamp_and_money_types_preserve_unknown_semantics() -> None:
    sessions = Base.metadata.tables["payment_sessions"]
    created_type = sessions.c.created_at.type
    expires_type = sessions.c.expires_at.type

    assert isinstance(sessions.c.amount.type, BigInteger)
    assert isinstance(sessions.c.adjusted_fee.type, BigInteger)
    assert isinstance(created_type, DateTime)
    assert isinstance(expires_type, DateTime)
    assert created_type.timezone is False
    assert expires_type.timezone is False


def test_merchant_scope_and_try_identity_are_database_constraints() -> None:
    session_constraints = {
        constraint.name for constraint in Base.metadata.tables["payment_sessions"].constraints
    }
    try_constraints = {
        constraint.name for constraint in Base.metadata.tables["payment_tries"].constraints
    }

    assert "fk_payment_sessions_terminal_merchant" in session_constraints
    assert "fk_payment_tries_session_merchant" in try_constraints
    assert "uq_payment_tries_session_seq" in try_constraints


def test_analytics_indexes_start_with_merchant_scope() -> None:
    for table_name in ("payment_sessions", "payment_tries"):
        indexes = Base.metadata.tables[table_name].indexes
        for index in indexes:
            if index.name and index.name.startswith(f"ix_{table_name}_merchant_"):
                assert list(index.columns)[0].name == "merchant_id"
