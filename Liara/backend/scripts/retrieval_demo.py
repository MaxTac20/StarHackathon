from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.services.corpus import embed_unembedded_chunks, load_corpus_jsonl
from app.services.embeddings import OpenRouterEmbeddingClient
from app.services.retrieval import retrieve

EMBEDDING_PRICE_PER_MILLION_TOKENS_USD = 0.01


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load a corpus fixture and run hybrid retrieval")
    parser.add_argument("corpus", type=Path)
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=5)
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    async with SessionLocal() as session:
        load_stats = await load_corpus_jsonl(session, args.corpus)
        async with OpenRouterEmbeddingClient.from_settings() as embedding_client:
            embedding_stats = await embed_unembedded_chunks(session, embedding_client)
            retrieval_run = await retrieve(
                session,
                embedding_client,
                args.query,
                top_k=args.top_k,
            )

    embedded_cost = (
        embedding_stats.total_tokens * EMBEDDING_PRICE_PER_MILLION_TOKENS_USD / 1_000_000
    )
    cost_per_1000_chunks = (
        embedded_cost * 1000 / embedding_stats.chunks if embedding_stats.chunks else 0.0
    )
    output = {
        "loaded_records": load_stats.records,
        "embedded_chunks": embedding_stats.chunks,
        "embedding_prompt_tokens": embedding_stats.prompt_tokens,
        "embedding_total_tokens": embedding_stats.total_tokens,
        "embedding_api_latency_seconds": round(embedding_stats.api_latency_seconds, 4),
        "embedding_wall_seconds": round(embedding_stats.wall_seconds, 4),
        "embedding_cost_usd": embedded_cost,
        "estimated_cost_per_1000_chunks_usd": cost_per_1000_chunks,
        "query": args.query,
        "query_variants": retrieval_run.query_variants,
        "query_embedding_tokens": retrieval_run.embedding_tokens,
        "query_embedding_latency_seconds": round(
            retrieval_run.embedding_latency_seconds,
            4,
        ),
        "results": [
            {
                "rank": rank,
                "id": result.id,
                "cite_url": result.cite_url,
                "score": result.score,
                "dense_rank": result.dense_rank,
                "lexical_rank": result.lexical_rank,
            }
            for rank, result in enumerate(retrieval_run.results, start=1)
        ],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


def main() -> None:
    asyncio.run(run(parse_args()))


if __name__ == "__main__":
    main()
