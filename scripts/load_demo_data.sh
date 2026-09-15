#!/usr/bin/env bash
# Uploads all demo contracts (demo-data/contracts/*.pdf) to kick off the
# pipeline. Run after `terraform apply` and `scripts/init_db.sql`.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_ROOT/infra/terraform"
RAW_BUCKET="$(terraform output -raw raw_contracts_bucket)"
cd "$REPO_ROOT"

echo "== Uploading demo contracts =="
for f in demo-data/contracts/*.pdf; do
  base="$(basename "$f" .pdf)"
  category="${base%%__*}"
  rest="${base#*__}"
  vendor="${rest%%__*}"
  aws s3 cp "$f" "s3://$RAW_BUCKET/raw/$category/$vendor/$base.pdf"
done

echo "Done. Watch the Step Functions console for pipeline runs, or poll GET /contracts."
