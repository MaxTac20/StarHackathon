from pathlib import Path

from app.schemas.corpus import CorpusRecord
from app.utils.persian import normalize

FIXTURE = Path(__file__).parents[1] / "fixtures" / "corpus.jsonl"


def test_fixture_matches_corpus_contract_and_normalization() -> None:
    lines = FIXTURE.read_text(encoding="utf-8").splitlines()
    records = [CorpusRecord.model_validate_json(line) for line in lines]

    assert len(records) >= 5
    assert all(record.text_norm == normalize(record.text) for record in records)
    assert all(record.cite_url.startswith("https://docs.liara.ir/") for record in records)
