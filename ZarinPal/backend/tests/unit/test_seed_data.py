from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any

import pytest

from app.cli.seed_data import (
    CSV_COLUMNS,
    SeedError,
    SourceFile,
    _existing_import_state,
    inspect_source,
    psycopg_connection_url,
)


def write_csv(path: Path, header: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.writer(target)
        writer.writerow(header)


def test_inspect_source_validates_header_and_hashes_file(tmp_path: Path) -> None:
    source_path = tmp_path / "payments.csv"
    write_csv(source_path, list(CSV_COLUMNS))

    source = inspect_source(source_path)

    assert source.filename == "payments.csv"
    assert source.size_bytes == source_path.stat().st_size
    assert source.sha256 == hashlib.sha256(source_path.read_bytes()).hexdigest()


def test_inspect_source_rejects_wrong_header_without_echoing_it(tmp_path: Path) -> None:
    source_path = tmp_path / "payments.csv"
    write_csv(source_path, ["payer_card_key", "secret-card-token"])

    with pytest.raises(SeedError) as error:
        inspect_source(source_path)

    assert "header" in str(error.value)
    assert "secret-card-token" not in str(error.value)


def test_connection_url_removes_sqlalchemy_driver() -> None:
    result = psycopg_connection_url("postgresql+psycopg://app:secret@localhost:5435/app")

    assert result == "postgresql://app:secret@localhost:5435/app"


def test_connection_url_rejects_non_postgresql_database() -> None:
    with pytest.raises(SeedError, match="PostgreSQL"):
        psycopg_connection_url("sqlite:///local.db")


class Result:
    def __init__(self, rows: list[tuple[Any, ...]]) -> None:
        self.rows = rows

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self.rows

    def fetchone(self) -> tuple[Any, ...] | None:
        return self.rows[0] if self.rows else None


class ExistingStateConnection:
    def __init__(self, imports: list[tuple[Any, ...]], has_rows: bool) -> None:
        self.results = iter((Result(imports), Result([(has_rows,)])))

    def execute(self, _query: str) -> Result:
        return next(self.results)


@pytest.mark.parametrize(
    ("imports", "has_rows", "expected"),
    [
        ([], False, "empty"),
        ([("same",)], True, "same"),
        ([("different",)], True, "different"),
        ([], True, "different"),
    ],
)
def test_existing_import_state(
    imports: list[tuple[Any, ...]], has_rows: bool, expected: str
) -> None:
    source = SourceFile(Path("ignored.csv"), "ignored.csv", 1, "same")

    result = _existing_import_state(ExistingStateConnection(imports, has_rows), source)  # type: ignore[arg-type]

    assert result == expected
