"""Thin wrappers around Bedrock InvokeModel for embeddings and Claude calls.

All calls go through the regional bedrock-runtime VPC endpoint - no
Bedrock traffic (which includes contract text) leaves the AWS network or
the deployment region.
"""
import json
import os

import boto3

_client = boto3.client("bedrock-runtime")


# Titan Text Embeddings V2 (the model this project targets, given the
# 1024-dim vector column and this request shape) accepts up to 50,000
# characters / 8,192 tokens. Chunking already keeps chunks well under
# this, but truncating here (rather than letting the API reject an
# oversized call) is a cheap backstop for the sliding-window fallback
# path and for ad-hoc query text.
_MAX_EMBED_CHARS = 50_000


def embed_text(text: str) -> list[float]:
    model_id = os.environ["EMBEDDING_MODEL_ID"]
    body = json.dumps({"inputText": text[:_MAX_EMBED_CHARS]})
    resp = _client.invoke_model(
        modelId=model_id,
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    payload = json.loads(resp["body"].read())
    return payload["embedding"]


def invoke_claude(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
    model_id = os.environ["LLM_MODEL_ID"]
    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
    )
    resp = _client.invoke_model(
        modelId=model_id,
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    payload = json.loads(resp["body"].read())
    return payload["content"][0]["text"]


def extract_json(raw_text: str) -> dict:
    """Claude sometimes wraps JSON in prose or a ```json fence; pull the object out."""
    text = raw_text.strip()
    if "```" in text:
        text = text.split("```")[1]
        text = text[4:] if text.startswith("json") else text
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in model output: {raw_text!r}")
    return json.loads(text[start : end + 1])
