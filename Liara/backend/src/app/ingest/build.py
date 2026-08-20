from __future__ import annotations

import argparse
import json
import math
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path

from app.core.config import BACKEND_DIR, get_settings
from app.ingest.corpus import IngestReport, build_manifest, build_records
from app.ingest.models import CorpusRecord, ManifestInventory

EXPECTED_COMMIT = "31f2ef7"
DATA_DIR = BACKEND_DIR.parent / "data"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build Liara's retrieval corpus and manifest-key inventory."
    )
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        help="Pinned liara-cloud/docs checkout (defaults to INGEST_CORPUS_DIR).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_DIR / "corpus.jsonl",
        help="JSONL corpus output path.",
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=DATA_DIR / "manifest.json",
        help="Manifest-key inventory output path.",
    )
    args = parser.parse_args(argv)

    corpus_dir = args.corpus_dir or get_settings().ingest_corpus_dir
    if corpus_dir is None:
        parser.error("set INGEST_CORPUS_DIR or pass --corpus-dir")
    corpus_dir = corpus_dir.expanduser().resolve()
    _validate_layout(corpus_dir)
    commit = _snapshot_commit(corpus_dir)

    report = IngestReport()
    records = build_records(corpus_dir, commit=commit, report=report)
    manifest = build_manifest(corpus_dir, commit=commit)
    _write_jsonl(args.output, records)
    _write_manifest(args.manifest_output, manifest)
    _print_summary(args.output, args.manifest_output, records, manifest, report)
    return 0


def _validate_layout(corpus_dir: Path) -> None:
    required = (
        corpus_dir / "public" / "llms",
        corpus_dir / "src" / "pages",
        corpus_dir / "public" / "casts",
    )
    missing = [str(path) for path in required if not path.is_dir()]
    if missing:
        raise ValueError(f"invalid corpus layout; missing: {', '.join(missing)}")


def _snapshot_commit(corpus_dir: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(corpus_dir), "rev-parse", "--short=7", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    commit = result.stdout.strip()
    if commit != EXPECTED_COMMIT:
        raise ValueError(f"corpus is at {commit}, expected pinned snapshot {EXPECTED_COMMIT}")
    return commit


def _write_jsonl(output: Path, records: Sequence[CorpusRecord]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=output.parent,
        prefix=f".{output.name}.",
        delete=False,
    ) as temporary:
        temporary_path = Path(temporary.name)
        for record in records:
            temporary.write(record.model_dump_json())
            temporary.write("\n")
    temporary_path.replace(output)


def _write_manifest(output: Path, manifest: ManifestInventory) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=output.parent,
        prefix=f".{output.name}.",
        delete=False,
    ) as temporary:
        temporary_path = Path(temporary.name)
        json.dump(
            manifest.model_dump(mode="json"),
            temporary,
            ensure_ascii=False,
            indent=2,
        )
        temporary.write("\n")
    temporary_path.replace(output)


def _print_summary(
    corpus_output: Path,
    manifest_output: Path,
    records: Sequence[CorpusRecord],
    manifest: ManifestInventory,
    report: IngestReport,
) -> None:
    token_estimates = sorted(record.token_estimate for record in records)
    anchored = sum(record.anchor is not None for record in records)
    cast_chunks = sum(
        any(block.source == "cast" for block in record.code_blocks) for record in records
    )
    distribution = {
        "min": token_estimates[0],
        "p50": _percentile(token_estimates, 0.50),
        "p90": _percentile(token_estimates, 0.90),
        "p95": _percentile(token_estimates, 0.95),
        "max": token_estimates[-1],
    }
    print(f"corpus: {corpus_output}")
    print(f"chunks: {len(records)}")
    print(f"chunks_with_anchor: {anchored}")
    print(f"chunks_with_cast_commands: {cast_chunks}")
    print(f"cast_files_with_commands: {len(report.cast_snippets_by_id)}")
    print(f"cast_command_blocks: {sum(report.cast_snippets_by_id.values())}")
    print(f"casts_without_commands: {len(report.empty_cast_ids)}")
    print(
        "cast_ids_without_commands: "
        f"{json.dumps(sorted(report.empty_cast_ids), ensure_ascii=False, separators=(',', ':'))}"
    )
    print(f"credential_redactions: {report.redaction_count}")
    print(f"credential_redaction_pages: {len(report.redactions_by_page)}")
    shapes_json = json.dumps(
        dict(sorted(report.redactions_by_shape.items())),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    print(f"redactions_by_shape: {shapes_json}")
    redactions_json = json.dumps(
        dict(sorted(report.redactions_by_page.items())),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    print(f"redactions_by_page: {redactions_json}")
    print(f"token_estimates: {json.dumps(distribution, separators=(',', ':'))}")
    print(f"manifest: {manifest_output}")
    print(f"manifest_key_paths: {len(manifest.keys)}")


def _percentile(values: Sequence[int], fraction: float) -> int:
    index = max(0, math.ceil(len(values) * fraction) - 1)
    return values[index]


if __name__ == "__main__":
    raise SystemExit(main())
