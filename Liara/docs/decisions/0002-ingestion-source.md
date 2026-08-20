# 0002 — Ingest from the git repository: mirror text, MDX anchors, and casts

**Status:** accepted · 2026-08-20 (revised the same day — see *Revision* below)

## Context

Liara's documentation is available several ways, and they are not equivalent. The
original version of this record chose to crawl the rendered HTML. Measuring the sources
directly showed that choice rested on a premise that is false, so this record was
rewritten against measurement rather than inspection of a handful of files.

All numbers below come from `liara-cloud/docs` at commit `31f2ef7` (2026-08-15):
1,142 MDX pages, 1,142 mirror pages, 90 cast files.

## Decision

Ingest from **one pinned, blobless sparse clone of the docs repository**, joining three
files per page:

1. **`public/llms/<path>.md`** is the text substrate — clean markdown, real heading
   hierarchy, no JSX.
2. **`src/pages/<path>.mdx`** supplies deep-link anchors, joined onto the mirror's
   headings by `<Section title>` → heading text.
3. **`public/casts/<id>.cast`** supplies the CLI commands that exist nowhere else,
   located via each page's `<Asciinema id>` references.

Path correspondence between (1) and (2) is exact: **1,142 of 1,142 pages pair, zero
missing.** No crawler, no headless browser, no network at ingest time.

## Why — what the measurement showed

| Property | `public/llms/*.md` | `src/pages/*.mdx` | Rendered HTML via `curl` |
|---|---|---|---|
| Prose | complete | complete | complete |
| `<Highlight>` code blocks | **3,724 of 3,729 — 99.9%** | 3,729 across 759 pages | **0** — client-rendered |
| Asciinema CLI commands | **0 of 124** | reference only; body lives in `.cast` | 0 |
| Section anchors | none | **790 ids across 525 pages** | top-level only |
| Reproducible | git pin | git pin | crawl output drifts |

Three premises in the original record were wrong:

- **"Rendered HTML has `<Highlight>` resolved to `<pre>`."** It does not. `docs.liara.ir`
  is a statically exported Next.js site whose `__NEXT_DATA__` is 188 bytes with empty
  `pageProps`; code blocks hydrate client-side. A `curl` of `paas/details/envs/` returns
  **zero** `<pre>` elements. Crawling would need a headless browser for every page —
  the most expensive option, chosen on the belief that it was the only complete one.
- **"The mirror has code-block dropout on ~27 pages."** It preserves 99.9% of fenced
  code. The real gap is narrower and sharper: **124 Asciinema casts across 80 pages
  (7.0%)**, which the mirror represents not at all.
- **"The mirror's `##` headings are tab labels, so structure is unusable."** Tab labels
  *are* headings, but the hierarchy above them is intact. `## OpenAI SDK → ### Python`
  and `## AI SDK → ### Python` are only ambiguous if the ancestry is discarded. Carrying
  the full heading path into the chunk resolves it.

The casts are not a consolation prize. `add-or-edit-envs-using-cli.cast` yields:

```
liara env:set --app django-application DEBUG=false
? Your app will be restarted due to these configuration changes. Confirm: Yes
Configuration variable applied and restarting django-application
```

— the command *and* its observable effect, which no code block on the site carries.
The first implementation read settled commands from `ESC]2;…BEL` window-title sequences,
but a full-corpus measurement found usable OSC-2 titles in only 32 of 90 cast files. Replay
every output event through `pyte` instead and read the resulting terminal screen: applying
cursor movement removes keystroke and autocompletion ghost text without discarding commands
from OSC-0-only or empty-title recordings. At this snapshot, replay recovers 108 command/result
blocks from 89 cast files; `create-drizzle-app.cast` is the sole final screen with no command.

## Consequences

- **Anchors join at 93.7%** — 740 of 790 `<Section id>` values match a mirror heading by
  title. Persian normalization (ZWNJ, yeh/kaf folding) does **not** improve this; the 49
  misses are genuine content divergence, where a self-closing `<Section />` marks a span
  whose visible headings are tab labels. Cite a section anchor when the join succeeds and
  fall back to the page URL when it does not. Never synthesize an anchor: ids are
  hand-authored English slugs (`see-envs`) for Persian headings
  (`مشاهده‌ی لیستی از متغیرهای محیطی تنظیم شده`), so no slug function can derive one.
- Chunk on the mirror's heading hierarchy, carrying the **full heading path**, not the leaf.
- Rewrite relative links to absolute at ingest using each page's `Original link:` header —
  otherwise citations from an isolated chunk are dead.
- Drop `/ai/ai-sdk-ui/chatbot.mdx`: a 296 KB base64 blob accounting for 11.2% of all chunk tokens.
- Pin the clone by commit in the ingest config so the golden set's scores stay comparable.
- Fetch with `--filter=blob:none --sparse` over `src/pages public/llms public/casts`:
  24 MB and seconds, against a full clone that exceeded two minutes on this connection.

## Revision — why this record changed

The first version was written from reading a sample of files and reasoning about what
each format *should* contain. Every correction above came from measuring all 1,142 pages
instead, which took about fifteen minutes. The reversal it was tested against — "read
the mirror instead of crawling" — turned out to be half right for reasons unrelated to
the ones proposed: the mirror is the better text substrate, but not because crawling is
brittle. Crawling simply does not return the code at all.
