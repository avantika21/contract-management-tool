"""Step 2: chunk the extracted text and store embeddings in pgvector."""
import os

import boto3

from common.bedrock import embed_text
from common.chunking import chunk_text
from common.db import get_connection, vector_literal

RAW_BUCKET = os.environ["RAW_BUCKET"]

s3 = boto3.client("s3")


def handler(event, context):
    contract_id = event["contract_id"]
    extracted_key = event["extracted_key"]

    obj = s3.get_object(Bucket=RAW_BUCKET, Key=extracted_key)
    text = obj["Body"].read().decode("utf-8")

    chunks = chunk_text(text)

    conn = get_connection()
    try:
        for idx, chunk in enumerate(chunks):
            embedding = embed_text(chunk)
            conn.run(
                """
                INSERT INTO contract_chunks (contract_id, chunk_index, content, embedding)
                VALUES (:contract_id, :chunk_index, :content, CAST(:embedding AS vector))
                """,
                contract_id=contract_id,
                chunk_index=idx,
                content=chunk,
                embedding=vector_literal(embedding),
            )
    finally:
        conn.close()

    event["chunk_count"] = len(chunks)
    return event
