from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from sqlalchemy import Select, desc, func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.models.document_chunk import DocumentChunk
from app.schemas.retrieval import RetrievedChunk
from app.services.embeddings import OpenRouterEmbeddingClient
from app.utils.persian import query_variants

DEFAULT_CANDIDATES_PER_LEG = 50
DEFAULT_RRF_K = 60
DEFAULT_DENSE_WEIGHT = 0.7
DEFAULT_LEXICAL_WEIGHT = 0.3

# ``simple`` deliberately has no stopword dictionary, so remove only a small,
# explicit set of Persian function words from queries. The index stays lossless.
_PERSIAN_FUNCTION_WORDS = frozenset(
    {
        "از",
        "اگر",
        "اما",
        "ان",
        "این",
        "با",
        "بر",
        "برای",
        "به",
        "بود",
        "تا",
        "چه",
        "چرا",
        "چطور",
        "چگونه",
        "در",
        "را",
        "روی",
        "شد",
        "شده",
        "شما",
        "شود",
        "کجا",
        "کدام",
        "که",
        "ما",
        "من",
        "می",
        "و",
        "یا",
        "یک",
        "است",
        "باشد",
        "هست",
        "هستند",
    }
)
_QUERY_EDGE_PUNCTUATION = "!\"'(),.:;<>?[\\]{}،؛؟«»…"


@dataclass(frozen=True)
class RankedChunk:
    id: str
    path: str
    cite_url: str
    heading_path: list[str]
    lang: str
    text: str
    leg_score: float


@dataclass(frozen=True)
class RetrievalRun:
    query_variants: list[str]
    results: list[RetrievedChunk]
    embedding_tokens: int
    embedding_latency_seconds: float


@dataclass
class _FusionState:
    chunk: RankedChunk
    score: float = 0.0
    dense_rank: int | None = None
    lexical_rank: int | None = None


async def retrieve(
    session: AsyncSession,
    embedding_client: OpenRouterEmbeddingClient,
    query: str,
    *,
    top_k: int = 10,
    candidates_per_leg: int = DEFAULT_CANDIDATES_PER_LEG,
) -> RetrievalRun:
    variants = query_variants(query)
    if not variants:
        return RetrievalRun(
            query_variants=[],
            results=[],
            embedding_tokens=0,
            embedding_latency_seconds=0.0,
        )

    query_embedding_batch = await embedding_client.embed_texts(variants)
    embeddings = [item.embedding for item in query_embedding_batch.items]
    dense = await dense_search(session, embeddings, limit=candidates_per_leg)
    # text_norm always strips ZWNJ, so only the first (stripped) variant can
    # match the lexical index. Dense retrieval still embeds both surface forms.
    lexical = await lexical_search(session, variants[0], limit=candidates_per_leg)
    results = reciprocal_rank_fusion(dense, lexical, top_k=top_k)
    return RetrievalRun(
        query_variants=variants,
        results=results,
        embedding_tokens=query_embedding_batch.total_tokens,
        embedding_latency_seconds=query_embedding_batch.latency_seconds,
    )


async def dense_search(
    session: AsyncSession,
    query_embeddings: list[list[float]],
    *,
    limit: int,
) -> list[RankedChunk]:
    best_by_id: dict[str, RankedChunk] = {}

    for embedding in query_embeddings:
        distance = DocumentChunk.embedding.cosine_distance(embedding).label("leg_score")
        statement = (
            select(DocumentChunk, distance)
            .where(DocumentChunk.embedding.is_not(None))
            .order_by(distance, DocumentChunk.id)
            .limit(limit)
        )
        rows = (await session.execute(statement)).all()
        for chunk, score in rows:
            candidate = _ranked_chunk(chunk, float(score))
            existing = best_by_id.get(candidate.id)
            if existing is None or candidate.leg_score < existing.leg_score:
                best_by_id[candidate.id] = candidate

    candidate_budget = limit * len(query_embeddings)
    return sorted(best_by_id.values(), key=lambda item: (item.leg_score, item.id))[
        :candidate_budget
    ]


async def lexical_search(
    session: AsyncSession,
    query_text: str,
    *,
    limit: int,
) -> list[RankedChunk]:
    statement = _lexical_statement(query_text, limit=limit)
    rows = (await session.execute(statement)).all()
    return [_ranked_chunk(chunk, float(score)) for chunk, score in rows]


def _lexical_statement(variant: str, *, limit: int) -> Select[tuple[DocumentChunk, float]]:
    simple: ColumnElement[str] = literal_column("'simple'")
    document = func.to_tsvector(simple, DocumentChunk.text_norm)
    query = func.websearch_to_tsquery(simple, _or_query_terms(variant))
    score = func.ts_rank_cd(document, query).label("leg_score")
    return cast(
        Select[tuple[DocumentChunk, float]],
        select(DocumentChunk, score)
        .where(document.op("@@")(query))
        .order_by(desc(score), DocumentChunk.id)
        .limit(limit),
    )


def _or_query_terms(variant: str) -> str:
    content_terms: list[str] = []
    for term in variant.split():
        comparison_term = term.strip(_QUERY_EDGE_PUNCTUATION)
        if comparison_term and comparison_term not in _PERSIAN_FUNCTION_WORDS:
            content_terms.append(term)
    return " OR ".join(content_terms)


def reciprocal_rank_fusion(
    dense: list[RankedChunk],
    lexical: list[RankedChunk],
    *,
    top_k: int,
    rrf_k: int = DEFAULT_RRF_K,
    dense_weight: float = DEFAULT_DENSE_WEIGHT,
    lexical_weight: float = DEFAULT_LEXICAL_WEIGHT,
) -> list[RetrievedChunk]:
    states: dict[str, _FusionState] = {}

    for rank, chunk in enumerate(dense, start=1):
        state = states.setdefault(chunk.id, _FusionState(chunk=chunk))
        state.score += dense_weight / (rrf_k + rank)
        state.dense_rank = rank

    for rank, chunk in enumerate(lexical, start=1):
        state = states.setdefault(chunk.id, _FusionState(chunk=chunk))
        state.score += lexical_weight / (rrf_k + rank)
        state.lexical_rank = rank

    ordered = sorted(
        states.values(),
        key=lambda state: (
            -state.score,
            min(state.dense_rank or 10**9, state.lexical_rank or 10**9),
            state.chunk.id,
        ),
    )
    return [
        RetrievedChunk(
            id=state.chunk.id,
            path=state.chunk.path,
            cite_url=state.chunk.cite_url,
            heading_path=state.chunk.heading_path,
            lang=state.chunk.lang,
            text=state.chunk.text,
            score=state.score,
            dense_rank=state.dense_rank,
            lexical_rank=state.lexical_rank,
        )
        for state in ordered[:top_k]
    ]


def _ranked_chunk(chunk: DocumentChunk, score: float) -> RankedChunk:
    return RankedChunk(
        id=chunk.id,
        path=chunk.path,
        cite_url=chunk.cite_url,
        heading_path=chunk.heading_path,
        lang=chunk.lang,
        text=chunk.text,
        leg_score=score,
    )
