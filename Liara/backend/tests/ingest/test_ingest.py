from pathlib import Path

from app.ingest.casts import extract_cast_snippets
from app.ingest.corpus import IngestReport, build_manifest, build_records
from app.ingest.models import CorpusRecord
from app.ingest.redact import PLACEHOLDER, redact_credentials

FIXTURE_CORPUS = Path(__file__).parent / "fixtures" / "corpus"


def test_cast_replay_removes_autosuggestion_noise_and_keeps_visible_result() -> None:
    snippets = extract_cast_snippets(FIXTURE_CORPUS / "public/casts/demo.cast")

    assert len(snippets) == 1
    assert snippets[0].command == "liara db create --plan=small-g2 --public-network"
    assert snippets[0].command.count("--plan=small-g2") == 1
    assert "Database my-db created." in snippets[0].result


def test_records_join_anchors_sniff_fences_and_keep_ancestry() -> None:
    report = IngestReport()
    records = build_records(FIXTURE_CORPUS, commit="31f2ef7", report=report)
    by_heading = {tuple(record.heading_path): record for record in records}

    first_python = by_heading[("راهنمای نمونه", "SDK اول", "Python")]
    second_python = by_heading[("راهنمای نمونه", "SDK دوم", "Python")]
    fallback = by_heading[("راهنمای نمونه", "عنوان متفاوت")]

    assert first_python.anchor == "first-sdk"
    assert first_python.cite_url.endswith("#first-sdk")
    assert any(block.source == "cast" for block in first_python.code_blocks)

    assert second_python.anchor == "second-sdk"
    assert first_python.heading_path != second_python.heading_path
    assert [block.lang for block in second_python.code_blocks] == ["bash", "json"]

    assert fallback.anchor is None
    assert fallback.cite_url == "https://docs.liara.ir/guides/sample/"
    assert len({record.id for record in records}) == len(records)
    assert report.empty_cast_ids == {"empty"}

    page_intro = by_heading[("راهنمای نمونه",)]
    assert "https://docs.liara.ir/guides/install" in page_intro.text
    assert "https://docs.liara.ir/guides/logo.png" in page_intro.text
    assert "https://docs.liara.ir/target" in page_intro.text
    serialized = "\n".join(record.model_dump_json() for record in records)
    for secret in (
        "DemoPassword123!",
        "UriPassword456!",
        "hunter2",
        # Deliberately not shaped like any real provider's key. A fixture that
        # looks like a live Stripe or AWS credential trips GitHub's push
        # protection and blocks the repository, and a reader cannot tell it from
        # a real leak. The redactor keys on entropy and position, so a synthetic
        # token exercises it just as well.
        "examplenotarealtoken7Qw3Zx9Lm2Rt8Vb4",
    ):
        assert secret not in serialized
    assert serialized.count(PLACEHOLDER) >= 4
    assert "liara init -P python" in second_python.text
    assert report.redaction_count == 4
    assert report.redactions_by_page == {"guides/sample": 4}
    assert report.redactions_by_shape == {
        "high_entropy": 1,
        "password_flag": 2,
        "uri_credential": 1,
    }
    for record in records:
        CorpusRecord.model_validate(record.model_dump())


def test_manifest_contains_only_parseable_liara_json_leaf_paths() -> None:
    manifest = build_manifest(FIXTURE_CORPUS, commit="31f2ef7")
    keys = {item.path: item for item in manifest.keys}

    assert set(keys) == {"port", "python.version"}
    assert keys["python.version"].frequency == 1
    assert keys["python.version"].example_pages == ["guides/sample"]


def test_redaction_does_not_treat_port_flags_or_placeholders_as_credentials() -> None:
    text = (
        "pg_restore -p 31567 -U root -d $DATABASE_NAME\n"
        f"mysql -p{PLACEHOLDER}\n"
        f"postgres://root:{PLACEHOLDER}@db.example.test/app\n"
        "'password' => env('DB_PASSWORD')"
    )

    result = redact_credentials(text)

    assert result.text == text
    assert result.count == 0


def test_redaction_is_idempotent_for_password_variables_with_matching_end_letters() -> None:
    text = (
        "mariadb -h DB_HOST -u DB_USER -pDB_PASSWORD < backup.sql\n"
        "sqlcmd -S DB_URL -Usa -P DB_PASSWORD"
    )

    first = redact_credentials(text)
    second = redact_credentials(first.text)

    assert first.text == (
        f"mariadb -h DB_HOST -u DB_USER -p{PLACEHOLDER} < backup.sql\n"
        f"sqlcmd -S DB_URL -Usa -P {PLACEHOLDER}"
    )
    assert first.counts_by_shape == {"password_flag": 2}
    assert second.text == first.text
    assert second.count == 0


def test_redaction_covers_audited_shapes_without_blanket_long_token_matching() -> None:
    fake_jwt = "eyJmYWtlIjp0cnVlfQ.ZmFrZS1wYXlsb2Fk.ZmFrZS1zaWduYXR1cmU"
    fake_password = "Ab3dEf5hIj7lMn9pQr2tUv4x"
    fake_pass_value = "QwertyUiopAsdfghJklZxcvb"
    fake_uuid = "00000000-0000-4000-8000-000000000000"
    fake_hex = "ab" * 30
    safe_values = ("password", "your-smtp-pass", "redisPassword", "Environment", "$uriParts")
    text = "\n".join(
        (
            f"Authorization: Bearer {fake_jwt}",
            f'password: "{fake_password}"',
            f"POSTGRESQL_DB_PASS={fake_pass_value}",
            f"MAIL_PASSWORD='{fake_uuid}'",
            f"SECRET_KEY   {fake_hex}",
            f"resource_id: {fake_uuid}",
            *(f"password: {value}" for value in safe_values),
            "Password: experimental_partialOutputStream",
            "restore-backup-into-mariadb-database-with-phpmyadmin",
            "experimental_partialOutputStream",
        )
    )

    result = redact_credentials(text)

    assert result.counts_by_shape == {
        "hex_secret": 1,
        "jwt": 1,
        "password_alphanumeric": 2,
        "password_uuid": 1,
    }
    assert result.text.count(PLACEHOLDER) == 5
    assert f"resource_id: {fake_uuid}" in result.text
    for safe_value in safe_values:
        assert f"password: {safe_value}" in result.text
    assert "Password: experimental_partialOutputStream" in result.text
    assert "restore-backup-into-mariadb-database-with-phpmyadmin" in result.text
    assert "experimental_partialOutputStream" in result.text
