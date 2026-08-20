from __future__ import annotations

import argparse
import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import psycopg
from psycopg import Connection, sql
from sqlalchemy.engine import make_url

from app.core.config import BACKEND_DIR, get_settings

PROJECT_DIR = BACKEND_DIR.parent
TRANSFORMATION_VERSION: Final = "1"
ADVISORY_LOCK_ID: Final = 20_260_820
CSV_COLUMNS: Final = (
    "session_key",
    "try_seq",
    "terminal_key",
    "merchant_key",
    "category_id",
    "category_title",
    "amount",
    "adjusted_fee",
    "session_status",
    "try_status",
    "switch_response_code",
    "psp_code",
    "issuer_bank_code",
    "payer_card_key",
    "verify_type",
    "init_time_ms",
    "verify_time_ms",
    "created_at",
    "try_created_at",
    "verified_at",
    "settled_at",
    "expire_in",
)


class SeedError(RuntimeError):
    """A safe-to-display seed failure that never contains a raw source row."""


@dataclass(frozen=True)
class SourceFile:
    path: Path
    filename: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class ImportCounts:
    source_rows: int
    sessions: int
    tries: int


def inspect_source(path: Path) -> SourceFile:
    resolved = path if path.is_absolute() else PROJECT_DIR / path
    resolved = resolved.resolve()
    if not resolved.is_file():
        raise SeedError(f"Seed CSV does not exist: {resolved}")

    try:
        with resolved.open("r", encoding="utf-8-sig", newline="") as source:
            header = next(csv.reader(source), None)
    except UnicodeDecodeError as exc:
        raise SeedError("Seed CSV header is not valid UTF-8") from exc

    if header != list(CSV_COLUMNS):
        raise SeedError("Seed CSV header does not match the required challenge dataset columns")

    digest = hashlib.sha256()
    with resolved.open("rb") as source_bytes:
        for chunk in iter(lambda: source_bytes.read(1024 * 1024), b""):
            digest.update(chunk)
    return SourceFile(
        path=resolved,
        filename=resolved.name,
        size_bytes=resolved.stat().st_size,
        sha256=digest.hexdigest(),
    )


def psycopg_connection_url(database_url: str) -> str:
    url = make_url(database_url)
    if not url.drivername.startswith("postgresql"):
        raise SeedError("DATABASE_URL must use PostgreSQL")
    return url.set(drivername="postgresql").render_as_string(hide_password=False)


def _create_staging_table(connection: Connection[tuple[object, ...]]) -> None:
    column_definitions = sql.SQL(",\n").join(
        sql.SQL("{} text").format(sql.Identifier(column_name)) for column_name in CSV_COLUMNS
    )
    connection.execute(
        sql.SQL(
            """
            CREATE TEMPORARY TABLE seed_payment_rows (
                source_row_number bigint GENERATED ALWAYS AS IDENTITY,
                {}
            ) ON COMMIT DROP
            """
        ).format(column_definitions)
    )


def _copy_source(connection: Connection[tuple[object, ...]], source: SourceFile) -> None:
    copy_columns = sql.SQL(", ").join(map(sql.Identifier, CSV_COLUMNS))
    copy_statement = sql.SQL(
        "COPY seed_payment_rows ({}) FROM STDIN WITH (FORMAT CSV, HEADER true, NULL '')"
    ).format(copy_columns)
    try:
        with connection.cursor().copy(copy_statement) as copy:
            with source.path.open("rb") as source_bytes:
                for chunk in iter(lambda: source_bytes.read(1024 * 1024), b""):
                    copy.write(chunk)
    except psycopg.Error as exc:
        raise SeedError(
            "PostgreSQL could not parse the CSV; no source values were written to logs"
        ) from exc


VALIDATIONS: Final[tuple[tuple[str, str], ...]] = (
    (
        "a required value is blank",
        """
        SELECT source_row_number FROM seed_payment_rows
        WHERE NULLIF(btrim(session_key), '') IS NULL
           OR NULLIF(btrim(try_seq), '') IS NULL
           OR NULLIF(btrim(terminal_key), '') IS NULL
           OR NULLIF(btrim(merchant_key), '') IS NULL
           OR NULLIF(btrim(category_id), '') IS NULL
           OR NULLIF(btrim(category_title), '') IS NULL
           OR NULLIF(btrim(amount), '') IS NULL
           OR NULLIF(btrim(adjusted_fee), '') IS NULL
           OR NULLIF(btrim(session_status), '') IS NULL
           OR NULLIF(btrim(try_status), '') IS NULL
           OR NULLIF(btrim(verify_type), '') IS NULL
           OR NULLIF(btrim(created_at), '') IS NULL
           OR NULLIF(btrim(expire_in), '') IS NULL
        LIMIT 1
        """,
    ),
    (
        "an integer is invalid or outside its database range",
        """
        SELECT source_row_number FROM seed_payment_rows
        WHERE NOT pg_input_is_valid(try_seq, 'smallint')
           OR NOT pg_input_is_valid(amount, 'bigint')
           OR NOT pg_input_is_valid(adjusted_fee, 'bigint')
           OR (init_time_ms IS NOT NULL AND NOT pg_input_is_valid(init_time_ms, 'integer'))
           OR (verify_time_ms IS NOT NULL AND NOT pg_input_is_valid(verify_time_ms, 'integer'))
           OR CASE WHEN pg_input_is_valid(try_seq, 'smallint')
                   THEN try_seq::smallint < 0 ELSE false END
           OR CASE WHEN pg_input_is_valid(amount, 'bigint') THEN amount::bigint < 0 ELSE false END
           OR CASE WHEN pg_input_is_valid(adjusted_fee, 'bigint')
                   THEN adjusted_fee::bigint < 0 ELSE false END
           OR CASE WHEN init_time_ms IS NOT NULL AND pg_input_is_valid(init_time_ms, 'integer')
                   THEN init_time_ms::integer < 0 ELSE false END
           OR CASE WHEN verify_time_ms IS NOT NULL AND pg_input_is_valid(verify_time_ms, 'integer')
                   THEN verify_time_ms::integer < 0 ELSE false END
        LIMIT 1
        """,
    ),
    (
        "a timestamp is invalid",
        """
        SELECT source_row_number FROM seed_payment_rows
        WHERE NOT pg_input_is_valid(created_at, 'timestamp without time zone')
           OR NOT pg_input_is_valid(expire_in, 'timestamp without time zone')
           OR (try_created_at IS NOT NULL AND
               NOT pg_input_is_valid(try_created_at, 'timestamp without time zone'))
           OR (verified_at IS NOT NULL AND
               NOT pg_input_is_valid(verified_at, 'timestamp without time zone'))
           OR (settled_at IS NOT NULL AND
               NOT pg_input_is_valid(settled_at, 'timestamp without time zone'))
        LIMIT 1
        """,
    ),
    (
        "a session status is unsupported",
        """
        SELECT source_row_number FROM seed_payment_rows
        WHERE session_status NOT IN ('Failed', 'Paid', 'Reversed', 'Verified')
        LIMIT 1
        """,
    ),
    (
        "a try status is unsupported",
        """
        SELECT source_row_number FROM seed_payment_rows
        WHERE try_status NOT IN ('Failed', 'InBank', 'NoAttempt', 'Paid', 'Reversed', 'Verified')
        LIMIT 1
        """,
    ),
    (
        "a verification type is unsupported",
        """
        SELECT source_row_number FROM seed_payment_rows
        WHERE verify_type NOT IN ('Automated', 'Manual')
        LIMIT 1
        """,
    ),
    (
        "the same session and try sequence occurs more than once",
        """
        SELECT min(source_row_number) FROM seed_payment_rows
        GROUP BY session_key, try_seq::smallint HAVING count(*) > 1 LIMIT 1
        """,
    ),
    (
        "session-level values change between retries",
        """
        SELECT min(source_row_number) FROM seed_payment_rows
        GROUP BY session_key
        HAVING count(DISTINCT (
            merchant_key, terminal_key, category_id, category_title, amount,
            adjusted_fee, session_status, verify_type, created_at, expire_in
        )) > 1
        LIMIT 1
        """,
    ),
    (
        "a category ID has multiple Persian titles",
        """
        SELECT min(source_row_number) FROM seed_payment_rows
        GROUP BY category_id HAVING count(DISTINCT category_title) > 1 LIMIT 1
        """,
    ),
)


def _validate_staging(connection: Connection[tuple[object, ...]]) -> None:
    for reason, query in VALIDATIONS:
        row = connection.execute(query).fetchone()
        if row is not None and row[0] is not None:
            csv_row = int(str(row[0])) + 1  # Identity starts at one; header is line one.
            raise SeedError(f"CSV row {csv_row}: {reason}")


def _existing_import_state(connection: Connection[tuple[object, ...]], source: SourceFile) -> str:
    imports = connection.execute("SELECT sha256 FROM dataset_imports ORDER BY id").fetchall()
    has_rows = connection.execute(
        """
        SELECT EXISTS (SELECT 1 FROM merchants)
            OR EXISTS (SELECT 1 FROM merchant_categories)
            OR EXISTS (SELECT 1 FROM terminals)
            OR EXISTS (SELECT 1 FROM payment_sessions)
            OR EXISTS (SELECT 1 FROM payment_tries)
        """
    ).fetchone()
    dataset_has_rows = bool(has_rows and has_rows[0])
    if len(imports) == 1 and imports[0][0] == source.sha256:
        return "same"
    if imports or dataset_has_rows:
        return "different"
    return "empty"


def _replace_dataset(connection: Connection[tuple[object, ...]]) -> None:
    connection.execute(
        """
        TRUNCATE TABLE
            payment_tries, payment_sessions, terminals, merchants,
            merchant_categories, dataset_imports
        RESTART IDENTITY
        """
    )


def _normalize_staging(
    connection: Connection[tuple[object, ...]], source: SourceFile
) -> ImportCounts:
    counts_row = connection.execute(
        "SELECT count(*), count(DISTINCT session_key) FROM seed_payment_rows"
    ).fetchone()
    assert counts_row is not None
    source_rows, session_count = int(str(counts_row[0])), int(str(counts_row[1]))
    import_row = connection.execute(
        """
        INSERT INTO dataset_imports (
            source_filename, sha256, source_size_bytes, source_row_count,
            session_count, try_count, transformation_version
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            source.filename,
            source.sha256,
            source.size_bytes,
            source_rows,
            session_count,
            source_rows,
            TRANSFORMATION_VERSION,
        ),
    ).fetchone()
    assert import_row is not None
    import_id = int(str(import_row[0]))

    connection.execute(
        """
        INSERT INTO merchants (import_id, merchant_key)
        SELECT %s, merchant_key FROM seed_payment_rows GROUP BY merchant_key
        """,
        (import_id,),
    )
    connection.execute(
        """
        INSERT INTO merchant_categories (category_id, import_id, title_fa)
        SELECT category_id, %s, min(category_title)
        FROM seed_payment_rows GROUP BY category_id
        """,
        (import_id,),
    )
    connection.execute(
        """
        INSERT INTO terminals (import_id, merchant_id, terminal_key)
        SELECT %s, merchants.id, staged.terminal_key
        FROM (
            SELECT merchant_key, terminal_key FROM seed_payment_rows
            GROUP BY merchant_key, terminal_key
        ) AS staged
        JOIN merchants USING (merchant_key)
        """,
        (import_id,),
    )
    connection.execute(
        """
        INSERT INTO payment_sessions (
            import_id, session_key, merchant_id, terminal_id, category_id,
            amount, adjusted_fee, session_status, verify_type, created_at, expires_at
        )
        SELECT
            %s, staged.session_key, merchants.id, terminals.id, staged.category_id,
            staged.amount::bigint, staged.adjusted_fee::bigint, staged.session_status,
            staged.verify_type, staged.created_at::timestamp, staged.expire_in::timestamp
        FROM (
            SELECT DISTINCT ON (session_key)
                session_key, merchant_key, terminal_key, category_id, amount,
                adjusted_fee, session_status, verify_type, created_at, expire_in
            FROM seed_payment_rows ORDER BY session_key, source_row_number
        ) AS staged
        JOIN merchants USING (merchant_key)
        JOIN terminals
          ON terminals.merchant_id = merchants.id
         AND terminals.terminal_key = staged.terminal_key
        """,
        (import_id,),
    )
    connection.execute(
        """
        INSERT INTO payment_tries (
            session_id, merchant_id, try_seq, try_status, switch_response_code,
            psp_code, issuer_bank_code, payer_card_key, init_time_ms, verify_time_ms,
            try_created_at, verified_at, settled_at
        )
        SELECT
            sessions.id, sessions.merchant_id, staged.try_seq::smallint,
            staged.try_status, staged.switch_response_code, staged.psp_code,
            staged.issuer_bank_code, staged.payer_card_key,
            staged.init_time_ms::integer, staged.verify_time_ms::integer,
            staged.try_created_at::timestamp, staged.verified_at::timestamp,
            staged.settled_at::timestamp
        FROM seed_payment_rows AS staged
        JOIN payment_sessions AS sessions USING (session_key)
        """
    )
    return ImportCounts(source_rows=source_rows, sessions=session_count, tries=source_rows)


def seed_database(source: SourceFile, *, replace: bool) -> ImportCounts | None:
    settings = get_settings()
    if settings.database_url is None:
        raise SeedError("DATABASE_URL could not be assembled")
    connection_url = psycopg_connection_url(settings.database_url)

    try:
        with psycopg.connect(connection_url) as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (ADVISORY_LOCK_ID,))
            state = _existing_import_state(connection, source)
            if not replace and state == "same":
                return None
            if not replace and state == "different":
                raise SeedError(
                    "A different or untracked dataset already exists; "
                    "use make db-reseed to replace it"
                )
            if replace:
                _replace_dataset(connection)
            _create_staging_table(connection)
            _copy_source(connection, source)
            _validate_staging(connection)
            return _normalize_staging(connection, source)
    except SeedError:
        raise
    except psycopg.Error as exc:
        raise SeedError("Database seeding failed; the transaction was rolled back") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load the local ZarinPal challenge CSV")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="transactionally replace the existing imported dataset",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = get_settings()
    try:
        source = inspect_source(settings.seed_data_path)
        print(f"Seed source: {source.filename} (sha256 {source.sha256})", flush=True)
        print("Loading and validating the dataset transactionally...", flush=True)
        counts = seed_database(source, replace=bool(args.replace))
    except SeedError as exc:
        print(f"Seed failed: {exc}")
        return 1

    if counts is None:
        print("Seed skipped: this exact dataset is already loaded.")
    else:
        print(
            "Seed complete: "
            f"{counts.source_rows:,} source rows, {counts.sessions:,} sessions, "
            f"{counts.tries:,} payment tries."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
