"""Hybrid (vector + keyword) chunk retrieval for a contract.

Vector-only search on the 1200-word blended chunks this project used to
produce could miss clauses whose exact terminology (a defined term, a
section heading like "GOVERNING LAW") ranks below semantically-similar
but off-target prose. Postgres full-text search catches those exact-term
matches; vector search catches paraphrases keyword search misses
entirely. Combining the two by rank (Reciprocal Rank Fusion) avoids
having to normalize cosine distance against ts_rank, which live on
incomparable scales - a standard, parameter-light way to blend them.

`content_tsv` (a generated tsvector column, GIN-indexed) is created in
scripts/init_db.sql.
"""
from common.bedrock import embed_text
from common.db import vector_literal

RRF_K = 60
DEFAULT_CANDIDATE_POOL = 20

# Optional cosine-distance cutoff for the vector leg, so a contract with
# nothing relevant to a query doesn't always contribute its 3 "closest"
# (but potentially unrelated) chunks. Left disabled (None) by default:
# Titan's cosine-distance distribution hasn't been measured against this
# corpus, and an uncalibrated cutoff risks silently dropping genuinely
# relevant chunks in a way that's hard to notice without an eval set.
# Enable by passing e.g. max_distance=0.75 once you have real query/chunk
# examples to check a threshold against.
DEFAULT_MAX_DISTANCE = None


def _vector_search(conn, contract_id: str, query_embedding: str, limit: int, max_distance: float | None):
    where_distance = ""
    params = {"contract_id": contract_id, "query_embedding": query_embedding, "limit": limit}
    if max_distance is not None:
        where_distance = "AND embedding <=> CAST(:query_embedding AS vector) <= :max_distance"
        params["max_distance"] = max_distance

    rows = conn.run(
        f"""
        SELECT chunk_index, content
        FROM contract_chunks
        WHERE contract_id = :contract_id
        {where_distance}
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT :limit
        """,
        **params,
    )
    return [(chunk_index, content) for chunk_index, content in rows]


def _keyword_search(conn, contract_id: str, query_text: str, limit: int):
    rows = conn.run(
        """
        SELECT chunk_index, content
        FROM contract_chunks
        WHERE contract_id = :contract_id
          AND content_tsv @@ websearch_to_tsquery('english', :query_text)
        ORDER BY ts_rank(content_tsv, websearch_to_tsquery('english', :query_text)) DESC
        LIMIT :limit
        """,
        contract_id=contract_id,
        query_text=query_text,
        limit=limit,
    )
    return [(chunk_index, content) for chunk_index, content in rows]


def hybrid_search(
    conn,
    contract_id: str,
    query_text: str,
    limit: int,
    candidate_pool: int = DEFAULT_CANDIDATE_POOL,
    max_distance: float | None = DEFAULT_MAX_DISTANCE,
) -> list[tuple[int, str]]:
    """Return up to `limit` (chunk_index, content) pairs for `query_text`,
    ranked by Reciprocal Rank Fusion of a vector-similarity search and a
    Postgres keyword search, each over the top `candidate_pool` hits.
    """
    query_embedding = vector_literal(embed_text(query_text))
    vector_hits = _vector_search(conn, contract_id, query_embedding, candidate_pool, max_distance)
    keyword_hits = _keyword_search(conn, contract_id, query_text, candidate_pool)

    content_by_index = dict(vector_hits) | dict(keyword_hits)
    scores: dict[int, float] = {}
    for hits in (vector_hits, keyword_hits):
        for rank, (chunk_index, _content) in enumerate(hits):
            scores[chunk_index] = scores.get(chunk_index, 0.0) + 1.0 / (RRF_K + rank + 1)

    ranked_indexes = sorted(scores, key=lambda idx: scores[idx], reverse=True)[:limit]
    return [(idx, content_by_index[idx]) for idx in ranked_indexes]
