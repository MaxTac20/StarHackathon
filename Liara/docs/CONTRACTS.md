# CONTRACTS

The interfaces that let separate work streams proceed in parallel. Everything here is a
promise between streams: change it by editing this file and saying so, never by editing
one side to match the other.

## Corpus snapshot — do not re-clone

`liara-cloud/docs` is pinned at commit **`31f2ef7`** (default branch is `master`, not
`main`). A blobless sparse clone already exists on this machine; the path is in
`INGEST_CORPUS_DIR`. **Do not clone it again** — this connection runs at 25–50 KiB/s and
a full clone exceeds two minutes. If the directory is absent, recreate it with:

    git clone --filter=blob:none --sparse --depth 1 \
      https://github.com/liara-cloud/docs.git <dir>
    git -C <dir> sparse-checkout set src/pages public/llms public/casts indexer

Layout that matters, with exact 1:1 path correspondence between the first two:

| Path | Holds |
|---|---|
| `public/llms/<p>.md` | Clean markdown text. 1,142 files. Opens with an `Original link:` header |
| `src/pages/<p>.mdx` | Same page as JSX. Source of `<Section id>` anchors and `<Asciinema id>` refs |
| `public/casts/<id>.cast` | asciinema v2. 90 files, holding CLI commands present in no other source |

## Corpus record — `corpus.jsonl`

Produced by ingestion, consumed by retrieval. One JSON object per line, UTF-8, `\n`
terminated. Required fields:

```json
{
  "id": "paas/details/envs#add-envs:0",
  "path": "paas/details/envs",
  "url": "https://docs.liara.ir/paas/details/envs/",
  "anchor": "add-envs",
  "cite_url": "https://docs.liara.ir/paas/details/envs/#add-envs",
  "heading_path": ["متغیرهای محیطی", "نحوه اضافه‌کردن متغیرهای محیطی", "Liara CLI"],
  "lang": "fa",
  "text": "…",
  "text_norm": "…",
  "code_blocks": [{"lang": "bash", "source": "fence", "text": "…"}],
  "token_estimate": 412,
  "commit": "31f2ef7"
}
```

- `anchor` is `null` when the MDX join fails (about 6% of sections). `cite_url` then omits
  the fragment. **Never synthesize an anchor** — ids are hand-authored English slugs for
  Persian headings, so no slug function can derive one.
- `heading_path` carries the full ancestry, never just the leaf. Tab-label headings
  (`## NodeJS`, `### Python`) repeat within a page and are only disambiguated by ancestry.
- `text` is display text with ZWNJ intact. `text_norm` is folded for the lexical index.
- `code_blocks[].source` is `fence` or `cast`.

## Persian normalization

One implementation, shared by ingestion and query time, in the backend package.

- NFKC, then fold: `ي ى → ی`, `ك → ک`, `ة ە → ه`, `أ إ آ → ا`, `ؤ → و`, `ئ → ی`
- Delete tashkeel (U+064B–U+0652), tatweel (U+0640), and bidi marks (U+200E, U+200F)
- Map Persian (U+06F0–U+06F9) and Arabic-Indic (U+0660–U+0669) digits to ASCII
- **NFD is a trap.** `ۀ` decomposes to U+06D5 + U+0654, and U+06D5 is a *letter*, so
  mark-stripping silently changes the word. Never normalize to NFD.
- ZWNJ (U+200C) is deleted in `text_norm` only. At query time emit both the
  ZWNJ-preserving and ZWNJ-stripped variants — the corpus is inconsistent and neither
  policy dominates.

## Fence languages are unreliable

**156 of 570 `json`-labelled fences in the corpus are not JSON** — 27%. `paas/liarajson.md`
labels `liara init …` shell commands as `json`. Sniff content; never trust the label.

## Embeddings

`qwen/qwen3-embedding-8b` via OpenRouter, requested with `dimensions: 1024`. The native
4096 would exceed pgvector's HNSW limit of 2000. See `decisions/0001`.

## Streaming API

`POST /api/chat` returns `text/event-stream` in the **AI SDK v5 data-stream protocol**,
consumed by `useChat`. The frontend must render useful motion within 500 ms of the
request, because the driving model reasons before it speaks.

Wire framing is part of the contract:

- Every part is one SSE event framed as `data: <JSON>\n\n`; custom parts use
  `{"type":"data-<name>","data":<payload>}`.
- Responses carry `x-vercel-ai-ui-message-stream: v1`.
- Every stream terminates with `data: [DONE]\n\n`, including after a user-safe error
  part.

Beyond the standard text and reasoning parts, these custom parts are the contract:

| Part | Payload | When |
|---|---|---|
| `data-status` | `{ "phase": "...", "label": "..." }` | Each pipeline stage, as it starts |
| `data-sources` | `[{ "title", "cite_url", "path" }]` | Once retrieval settles, before generation |
| `data-notice` | `{ "kind": "defect" \| "gap", "text" }` | A named documentation defect, per `decisions/0004` |

`phase` values are a closed set: `understanding`, `retrieving`, `reading`, `drafting`.
Any other value must render as generic progress rather than breaking the UI.

Errors terminate the stream with an error part carrying a user-safe message. Never leak a
provider payload, a stack trace, or a key fragment into the stream.

## Secrets

`OPENROUTER_API_KEY` is read from the environment via `core/config.py`. It never appears
in a `VITE_*` variable, in the repository, in a log line, or in a stream event.
