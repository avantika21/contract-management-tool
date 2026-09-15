"""Step 1: pull raw text out of the uploaded contract PDF via Textract.

Expects contracts to be uploaded under `raw/<vendor>/<file>.pdf` in the raw
bucket. Category is populated later by field extraction.
"""
import os
import time
import uuid

import boto3

from common.db import get_connection

RAW_BUCKET = os.environ["RAW_BUCKET"]
POLL_INTERVAL_SECONDS = 5

textract = boto3.client("textract")
s3 = boto3.client("s3")


def _run_textract(bucket: str, key: str) -> str:
    job = textract.start_document_text_detection(
        DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}}
    )
    job_id = job["JobId"]

    while True:
        resp = textract.get_document_text_detection(JobId=job_id)
        status = resp["JobStatus"]
        if status == "SUCCEEDED":
            break
        if status == "FAILED":
            raise RuntimeError(f"Textract job {job_id} failed: {resp.get('StatusMessage')}")
        time.sleep(POLL_INTERVAL_SECONDS)

    lines: list[str] = []
    next_token = None
    while True:
        kwargs = {"JobId": job_id}
        if next_token:
            kwargs["NextToken"] = next_token
        resp = textract.get_document_text_detection(**kwargs)
        lines.extend(b["Text"] for b in resp.get("Blocks", []) if b["BlockType"] == "LINE")
        next_token = resp.get("NextToken")
        if not next_token:
            break

    return "\n".join(lines)


def handler(event, context):
    bucket = event["bucket"]
    key = event["key"]

    text = _run_textract(bucket, key)

    extracted_key = f"extracted/{key.removeprefix('raw/')}.txt"
    s3.put_object(
        Bucket=RAW_BUCKET,
        Key=extracted_key,
        Body=text.encode("utf-8"),
        ServerSideEncryption="aws:kms",
    )

    contract_id = str(uuid.uuid4())

    conn = get_connection()
    try:
        conn.run(
            "INSERT INTO contracts (id, s3_key, status) VALUES (:id, :s3_key, 'processing')",
            id=contract_id,
            s3_key=key,
        )
    finally:
        conn.close()

    return {
        "bucket": bucket,
        "key": key,
        "extracted_key": extracted_key,
        "contract_id": contract_id,
    }
