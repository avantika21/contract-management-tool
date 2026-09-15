"""Shared Postgres connection helper.

Uses pg8000 (pure Python, no compiled extension) so the Lambda dependency
layer builds with a plain `pip install` on any platform. Credentials are
pulled from Secrets Manager rather than baked into environment variables.
"""
import json
import os

import boto3
import pg8000.native

_secret_cache = None


def _get_secret() -> dict:
    global _secret_cache
    if _secret_cache is None:
        client = boto3.client("secretsmanager")
        resp = client.get_secret_value(SecretId=os.environ["DB_SECRET_ARN"])
        _secret_cache = json.loads(resp["SecretString"])
    return _secret_cache


def get_connection() -> pg8000.native.Connection:
    secret = _get_secret()
    return pg8000.native.Connection(
        user=secret["username"],
        password=secret["password"],
        host=os.environ.get("DB_HOST") or secret.get("host"),
        port=int(os.environ.get("DB_PORT") or secret.get("port", 5432)),
        database=secret.get("dbname", "contracts"),
        ssl_context=True,  # enforce TLS to Aurora
    )


def vector_literal(embedding: list[float]) -> str:
    """Render a Python float list as a pgvector literal, e.g. '[0.1,0.2,...]'."""
    return "[" + ",".join(f"{v:.8f}" for v in embedding) + "]"
