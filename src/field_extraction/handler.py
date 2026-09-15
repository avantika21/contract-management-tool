"""Step 3: retrieve the passages likely to hold key facts, then have the
LLM extract literal values from them (not the whole document - just the
chunks a vector search says are relevant to each fact we care about).
"""
from common.bedrock import extract_json, invoke_claude
from common.db import get_connection
from common.prompts import FIELD_EXTRACTION_SYSTEM_PROMPT, build_field_extraction_prompt
from common.retrieval import hybrid_search

TARGET_QUERIES = [
    "contract effective date and expiry date",
    "automatic renewal and renewal notice period",
    "termination rights and termination notice period",
    "liability cap and limitation of liability",
    "governing law and jurisdiction",
    "vendor / supplier / counterparty name and parties to the agreement",
    "total contract value, fees, pricing, and payment terms",
    "minimum purchase commitment, minimum volume, or price escalation",
]

CHUNKS_PER_QUERY = 3


def _retrieve_relevant_chunks(conn, contract_id: str) -> list[tuple[int, str]]:
    seen: dict[int, str] = {}
    for query in TARGET_QUERIES:
        for chunk_index, content in hybrid_search(conn, contract_id, query, limit=CHUNKS_PER_QUERY):
            seen[chunk_index] = content
    return list(seen.items())


def handler(event, context):
    contract_id = event["contract_id"]

    conn = get_connection()
    try:
        relevant_chunks = _retrieve_relevant_chunks(conn, contract_id)
    finally:
        conn.close()

    context_chunks = [content for _chunk_index, content in relevant_chunks]
    prompt = build_field_extraction_prompt(context_chunks)
    raw_response = invoke_claude(FIELD_EXTRACTION_SYSTEM_PROMPT, prompt)
    parsed = extract_json(raw_response)

    # Pull the model's excerpt citations out of the schema response and
    # resolve them against the numbered excerpts it was shown, so each
    # field can be traced back to the exact stored chunk it came from.
    field_citations = parsed.pop("field_citations", {}) or {}
    excerpts = [
        {"ref": i, "chunk_index": chunk_index, "content": content}
        for i, (chunk_index, content) in enumerate(relevant_chunks, start=1)
    ]

    event["extracted_fields"] = parsed
    event["extraction_sources"] = {"citations": field_citations, "excerpts": excerpts}
    return event
