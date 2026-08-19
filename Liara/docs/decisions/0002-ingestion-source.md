# 0002 — Ingest from rendered HTML, not MDX source or the markdown mirror

**Status:** accepted · 2026-08-20

## Context

Liara's documentation is available three ways, and they are not equivalent.

## Decision

Crawl the **rendered HTML** at the docs site.

## Why

| Source | Code blocks | Structure | Verdict |
|---|---|---|---|
| `src/pages/*.mdx` | **0 fenced blocks** — code is inside `<Highlight>` template literals | **0 `##` headings** — structure is `<Section id title>`; JSX in 1,141/1,142 files | A markdown splitter finds nothing to split on and embeds React boilerplate; imports and JSX are 40% of the bytes |
| `public/llms/*.md` mirror | Present, but **dropout on ~27 pages** including `paas/details/envs.md`, the most-linked page in the corpus | `##` headings present, but they are tab labels — `## NodeJS` appears five times on one page meaning five different things | Clean but lossy |
| **Rendered HTML** | `<Highlight>` resolved to `<pre>` | `<Section id>` is a real anchor | Complete *and* structured |

The anchor is the deciding factor: it yields **deep links to the exact section**, which
serves the "ارائه منبع مناسب" scored sub-criterion directly. Liara's own documentation
indexer crawls rendered HTML for the same reason.

## Consequences

- Chunk on `<Section>`, falling back to H1 plus size packing.
- Rewrite relative links to absolute at ingest, using each page's `Original link:` header
  — otherwise citations from an isolated chunk are dead.
- Drop `/ai/ai-sdk-ui/chatbot.mdx`: a 296 KB base64 blob accounting for 11.2% of all
  chunk tokens.
- Crawling is slower and more brittle than reading files. Snapshot the crawl output and
  version it, so the corpus is reproducible and the golden set's scores stay comparable.
