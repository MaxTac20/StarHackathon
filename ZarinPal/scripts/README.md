# Dataset download script

`download_data.sh` downloads the compressed ZarinPal challenge dataset, validates the
gzip archive, and extracts it into the project-local `data/` directory.

Run it from the ZarinPal project root:

```bash
make data-download
```

The command creates these ignored files:

```text
data/challenge_data.csv.gz
data/challenge_data.csv
```

It is safe to run repeatedly: when the extracted CSV already exists, the script leaves
it untouched. To replace both files with a newly downloaded copy, run:

```bash
FORCE=1 make data-download
```

The script requires either `curl` (preferred) or `wget`, plus `gzip`.
