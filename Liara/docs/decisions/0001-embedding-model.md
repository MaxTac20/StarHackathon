# 0001 — BGE-M3 for embeddings, not OpenAI

**Status:** accepted · 2026-08-20

## Context

The corpus is 99.7% Persian prose with Latin identifiers and code embedded. The default
reflex for a RAG system is OpenAI `text-embedding-3-large`.

## Decision

Use **BAAI/bge-m3** via OpenRouter (1024 dims, MIT, 8k context).

## Why

On Persian MIRACL nDCG@10, measured from the MTEB results repository and cross-validated
against the BGE-M3 paper across three independent systems:

| Model | Persian nDCG@10 |
|---|---:|
| Qwen3-Embedding-8B | 62.57 |
| gemini-embedding-001 | 61.63 |
| **BAAI/bge-m3** | **61.38** |
| Cohere embed-multilingual-v3.0 | 60.96 |
| **openai/text-embedding-3-large** | **41.67** |
| openai/text-embedding-3-small | 27.24 |

For calibration, plain BM25 scores 44.15 on the FaMTEB retrieval aggregate — **above
OpenAI's small model**. The default choice is roughly 20 nDCG points down on this corpus.

Three secondary reasons: BGE-M3 emits **learned sparse weights alongside the dense
vector at no extra cost**, giving the lexical leg of hybrid retrieval for free and
outscoring BM25 on Persian 45.1 to 28.7; its XLM-R tokenizer is far more efficient on
Persian than cl100k; and 1024 dims stays under pgvector's 2,000-dim HNSW ceiling, which a
3072-dim model would breach entirely.

Cost is not a factor either way — **the whole corpus embeds for 1.7 cents**.

## Rejected

- **OpenAI** — see above.
- **Hakim**, the Persian-specific model. It leads FaMTEB *overall* at 73.81 vs BGE-M3's
  65.29, but that headline is driven by classification and clustering. On the retrieval
  column the ordering **inverts**: BGE-M3 43.38, Hakim 40.43. Do not pick a model off a
  leaderboard headline when only one of its columns is the job.
- **Cohere embed-v4.0** — scores *below its own v3.0* on Persian (56.78 vs 60.96).
  Surprising enough that we would want to reproduce it before relying on either.

## Caveat

MIRACL Persian is Wikipedia-domain and roughly half of FaMTEB is machine-translated or
synthetic. Rankings should transfer; absolute numbers will not. Validate on the golden set.

## Consequences

Changing the embedding model later is a **re-index, not a migration**. Treat it as a
schema decision.
