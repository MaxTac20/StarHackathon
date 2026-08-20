#!/usr/bin/env bash

set -euo pipefail

dataset_url='https://startech.s3.ir-thr-at1.arvanstorage.ir/other%2Fchallenge_data.csv.gz?versionId='
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd -- "$script_dir/.." && pwd)"
data_dir="$project_dir/data"
archive_path="$data_dir/challenge_data.csv.gz"
dataset_path="$data_dir/challenge_data.csv"
download_path="$archive_path.download"
extract_path="$dataset_path.extract"

if [[ -f "$dataset_path" && "${FORCE:-0}" != '1' ]]; then
  printf 'Dataset already exists at %s\n' "$dataset_path"
  printf 'Set FORCE=1 to download it again.\n'
  exit 0
fi

mkdir -p "$data_dir"
trap 'rm -f "$download_path" "$extract_path"' EXIT

printf 'Downloading ZarinPal challenge dataset...\n'
if command -v curl >/dev/null 2>&1; then
  curl --fail --location --retry 3 --retry-all-errors --output "$download_path" "$dataset_url"
elif command -v wget >/dev/null 2>&1; then
  wget --output-document="$download_path" "$dataset_url"
else
  printf 'Error: install curl or wget to download the dataset.\n' >&2
  exit 1
fi

gzip --test "$download_path"
gzip --decompress --stdout "$download_path" > "$extract_path"

mv "$download_path" "$archive_path"
mv "$extract_path" "$dataset_path"

printf 'Downloaded archive: %s\n' "$archive_path"
printf 'Extracted dataset: %s\n' "$dataset_path"
