"""Procurement-facing read API: list/search contracts, fetch one, ask
ad-hoc questions of a specific contract (RAG over its stored chunks), and
issue presigned upload/download URLs so the frontend can push a PDF straight
to S3 (which is what kicks off the ingestion pipeline) and let users open
the original file straight from S3.

API Gateway HTTP API (v2) Lambda proxy integration; auth is enforced by
the Cognito JWT authorizer configured on the routes, not in this code.
"""
import json
import os
import re
import uuid

import boto3

from common.bedrock import invoke_claude
from common.db import get_connection
from common.prompts import QA_SYSTEM_PROMPT, build_qa_prompt
from common.retrieval import hybrid_search

RAW_BUCKET = os.environ.get("RAW_BUCKET", "")
UPLOAD_URL_TTL_SECONDS = 300
FILE_URL_TTL_SECONDS = 300
_SAFE_SEGMENT = re.compile(r"^[a-zA-Z0-9._-]+$")

s3 = boto3.client("s3")

CONTRACT_COLUMNS = """
    id, s3_key, vendor_name, category, status, effective_date, expiry_date,
    auto_renews, renewal_notice_days, termination_notice_days,
    termination_for_convenience, liability_cap_amount, liability_cap_currency,
    governing_law, data_residency_clause, contract_value_amount,
    contract_value_currency, payment_terms_days, pricing_model,
    minimum_commitment, price_escalation_clause, sla_summary,
    exclusivity_clause, change_of_control_clause, insurance_requirements,
    indemnification_summary, extraction_sources,
    created_at, updated_at
"""


def _response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }


def _row_to_contract(row, columns) -> dict:
    return dict(zip(columns, row))


def _list_contracts(conn, query_params: dict) -> dict:
    filters = []
    params = {}

    if category := query_params.get("category"):
        filters.append("category = :category")
        params["category"] = category

    if expiring_before := query_params.get("expiring_before"):
        filters.append("expiry_date <= :expiring_before")
        params["expiring_before"] = expiring_before

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    columns = [c.strip() for c in CONTRACT_COLUMNS.strip().split(",")]

    rows = conn.run(
        f"SELECT {CONTRACT_COLUMNS} FROM contracts {where_clause} ORDER BY created_at DESC LIMIT 100",
        **params,
    )
    return {"contracts": [_row_to_contract(r, columns) for r in rows]}


def _get_contract(conn, contract_id: str) -> dict | None:
    columns = [c.strip() for c in CONTRACT_COLUMNS.strip().split(",")]
    rows = conn.run(f"SELECT {CONTRACT_COLUMNS} FROM contracts WHERE id = :id", id=contract_id)
    if not rows:
        return None
    return _row_to_contract(rows[0], columns)


def _get_contract_file_url(conn, contract_id: str) -> dict | None:
    rows = conn.run("SELECT s3_key FROM contracts WHERE id = :id", id=contract_id)
    if not rows:
        return None
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": RAW_BUCKET, "Key": rows[0][0]},
        ExpiresIn=FILE_URL_TTL_SECONDS,
    )
    return {"url": url}


def _ask_contract(conn, contract_id: str, question: str) -> dict:
    hits = hybrid_search(conn, contract_id, question, limit=5)
    if not hits:
        return {"answer": "No indexed content found for this contract.", "sources": []}

    context_chunks = [content for _chunk_index, content in hits]
    prompt = build_qa_prompt(question, context_chunks)
    answer = invoke_claude(QA_SYSTEM_PROMPT, prompt, max_tokens=600)

    # `ref` matches the [n] citation numbers the model was given in the
    # prompt, so the frontend can resolve an in-answer citation to the
    # exact stored chunk it points at.
    sources = [
        {"ref": i, "chunk_index": chunk_index, "content": content}
        for i, (chunk_index, content) in enumerate(hits, start=1)
    ]
    return {"answer": answer, "sources": sources}


def _delete_contract(conn, contract_id: str) -> bool:
    rows = conn.run("SELECT s3_key FROM contracts WHERE id = :id", id=contract_id)
    if not rows:
        return False
    s3_key = rows[0][0]
    # contract_chunks rows cascade on the FK, so deleting the contract row is enough DB-side.
    conn.run("DELETE FROM contracts WHERE id = :id", id=contract_id)
    s3.delete_object(Bucket=RAW_BUCKET, Key=s3_key)
    return True


def _create_upload_url(body: dict) -> dict:
    vendor = body.get("vendor", "")
    filename = body.get("filename", "")

    if not _SAFE_SEGMENT.match(vendor or ""):
        raise ValueError("'vendor' must contain only letters, numbers, '.', '_' or '-'")
    if not filename.lower().endswith(".pdf") or not _SAFE_SEGMENT.match(filename.replace(" ", "_")):
        raise ValueError("'filename' must be a .pdf file name")

    # A random prefix keeps concurrent demo uploads of the same filename from colliding.
    key = f"raw/{vendor}/{uuid.uuid4().hex[:8]}-{filename}"
    url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": RAW_BUCKET, "Key": key, "ContentType": "application/pdf"},
        ExpiresIn=UPLOAD_URL_TTL_SECONDS,
    )
    return {"upload_url": url, "bucket": RAW_BUCKET, "key": key}


def handler(event, context):
    route_key = event.get("routeKey", "")
    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}

    if route_key == "POST /uploads":
        try:
            body = json.loads(event.get("body") or "{}")
            return _response(200, _create_upload_url(body))
        except ValueError as exc:
            return _response(400, {"error": str(exc)})

    conn = get_connection()
    try:
        if route_key == "GET /contracts":
            return _response(200, _list_contracts(conn, query_params))

        if route_key == "GET /contracts/{contract_id}":
            contract = _get_contract(conn, path_params["contract_id"])
            if contract is None:
                return _response(404, {"error": "contract not found"})
            return _response(200, contract)

        if route_key == "GET /contracts/{contract_id}/file-url":
            result = _get_contract_file_url(conn, path_params["contract_id"])
            if result is None:
                return _response(404, {"error": "contract not found"})
            return _response(200, result)

        if route_key == "POST /contracts/{contract_id}/ask":
            body = json.loads(event.get("body") or "{}")
            question = body.get("question")
            if not question:
                return _response(400, {"error": "'question' is required"})
            return _response(200, _ask_contract(conn, path_params["contract_id"], question))

        if route_key == "DELETE /contracts/{contract_id}":
            if not _delete_contract(conn, path_params["contract_id"]):
                return _response(404, {"error": "contract not found"})
            return _response(200, {"deleted": True})

        return _response(404, {"error": "route not found"})
    finally:
        conn.close()
