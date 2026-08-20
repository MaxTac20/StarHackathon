# 0001 — Qwen3-Embedding-8B for embeddings

**Status:** accepted · 2026-08-20
**Supersedes:** an earlier version of this record that chose BAAI/bge-m3. See *Revision*.

## Context

The corpus is 99.7% Persian prose with Latin identifiers and code embedded. We are
API-only — the application is the only thing we host — so the model must be reachable
through OpenRouter.

## Decision

Use **`qwen/qwen3-embedding-8b`** via OpenRouter. 32k context, $0.01/M.

## Why

Persian MIRACL nDCG@10, extracted from the MTEB results repository and cross-validated
against the BGE-M3 paper, restricted to models OpenRouter actually serves:

| Model | Persian nDCG@10 | $/M | Context |
|---|---:|---:|---:|
| **qwen/qwen3-embedding-8b** | **62.57** | 0.01 | 32k |
| google/gemini-embedding-001 | 61.63 | 0.15 | 20k |
| baai/bge-m3 | 61.38 | 0.01 | 8k |
| google/gemini-embedding-2-preview | 58.83 | 0.20 | 8k |
| intfloat/multilingual-e5-large | 59.23 | 0.01 | 512 |
| voyageai/voyage-4-large | 55.33 | 0.12 | 32k |
| **openai/text-embedding-3-large** | **41.67** | 0.13 | 8k |
| openai/text-embedding-3-small | 27.24 | 0.02 | 8k |

Qwen3 wins on every axis available to us: highest measured Persian score, joint-cheapest
price, and 4× the context of the runner-up at that price.

**Cost is not a factor either way** — the whole 1.7M-token corpus embeds for under two
cents at $0.01/M. Optimize purely for quality.

## Revision — why this record changed

The first version chose **BAAI/bge-m3**, and its central argument was that BGE-M3 emits
**learned sparse weights alongside the dense vector at no extra cost**, supplying the
lexical leg of hybrid retrieval for free and outscoring BM25 on Persian 45.1 to 28.7.

**That advantage is unavailable to us.** OpenRouter's `/embeddings` endpoint returns a
flat dense float array; `encoding_format` accepts only `float` or `base64`. There is no
sparse output. Obtaining BGE-M3's sparse head would require self-hosting the model, which
is out of scope — we host the application and nothing else.

With the sparse head gone, BGE-M3 is simply a lower-scoring, shorter-context model at the
same price as Qwen3, so the decision inverts.

## Consequence: the lexical leg got weaker

The hybrid retrieval design assumed BGE-M3 sparse would carry the Persian lexical side.
It now falls to PostgreSQL `to_tsvector('simple', …)` over normalized text for **both**
scripts. Persian BM25 is genuinely weak (MIRACL 0.333 against dense's 0.480), which is
why fusion stays **dense-dominant at roughly α=0.7**. This is a real quality loss against
the original plan and it is unavoidable while API-only. See `DESIGN.md` §6.

## Rejected

- **OpenAI embeddings** — 41.67, roughly 20 nDCG points down. For calibration, plain BM25
  scores 44.15 on the FaMTEB retrieval aggregate, i.e. **above OpenAI's small model**.
- **BGE-M3** — see *Revision*.
- **Voyage**, despite a generous 200M-token free tier. `voyage-4-large` scores 55.33 on
  Persian and `voyage-4` 53.33, seven to nine points under Qwen3. The free tier buys
  nothing at our scale — the entire corpus costs two cents to embed and would consume
  under 1% of the allowance — so it is a measurable quality loss for no real saving.
  Voyage is strong on English and code retrieval; Persian is specifically where it is not.
- **Hakim**, the Persian-specific model. It leads FaMTEB *overall* (73.81 vs BGE-M3's
  65.29), but that headline is driven by classification and clustering. On the retrieval
  column the ordering **inverts**: BGE-M3 43.38, Hakim 40.43. Never pick a model off a
  leaderboard headline when only one of its columns is the job. Also not on OpenRouter.

## Newer is not automatically better for Persian

Two rows above make this concrete: `gemini-embedding-2-preview` scores **below** its own
predecessor `gemini-embedding-001` (58.83 vs 61.63), and `voyage-4-large`, a current and
strong general model, lands six points under a 2024 one. Persian is a minority language
and general-purpose embedders do not reliably improve on it release over release. Model
recency is not evidence; the Persian column is.

## Open — probe during checkpoint 1

Seven OpenRouter embedding models have **no published Persian data**, and two are free:

- `nvidia/nemotron-3-embed-1b:free` — 32k context, $0
- `nvidia/llama-nemotron-embed-vl-1b-v2:free` — 131k context, $0
- `perplexity/pplx-embed-v1-4b` — $0.03/M
- `google/gemini-embedding-2` — the non-preview release

If either free model is competitive on Persian, embedding cost goes to zero. Fold the
probe into checkpoint 1, where the chunked corpus and the golden questions already exist,
and measure on **our** corpus — MIRACL is Wikipedia-domain and its absolute numbers will
not transfer.

## Caveat

MIRACL Persian is Wikipedia-domain and roughly half of FaMTEB is machine-translated or
synthetic. Rankings should transfer; absolute numbers will not. Validate on the golden set.

## Consequences

Changing the embedding model later is a **re-index, not a migration**. Treat it as a
schema decision. At two cents per full re-index, running the probe is cheap; changing our
minds after launch is not.
