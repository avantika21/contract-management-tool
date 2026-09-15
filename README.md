# Contract Management Tool (RAG on AWS)

A procurement-focused contract review pipeline: upload a contract PDF,
get back structured fields — dates, termination terms, liability caps,
data residency clauses, plus commercial terms (contract value, payment
terms, pricing model, price escalation) and compliance terms (SLA
credits, exclusivity, change of control, insurance, indemnification) —
all searchable, none of it hand-typed, each field traceable back to the
contract excerpt it came from. The dashboard also surfaces spend under
management and upcoming renewal deadlines (expiry minus the contractual
notice period, not just the expiry date) so procurement can act before a
contract silently auto-renews.

Built AWS-native and single-region (**eu-west-2 / London**) throughout,
for teams that need to keep contract data verifiably in-region.

## Pipeline

```
S3 (raw/) --> EventBridge --> Step Functions
                                  |
                                  v
                 1. extraction         Textract OCR -> plain text in S3
                 2. chunk_embed        chunk text, embed (Bedrock Titan), store in pgvector
                 3. field_extraction   vector-search the relevant chunks, extract fields (Bedrock Claude)
                 4. store_results      write everything to the contracts table
```

Query side: API Gateway (Cognito-authenticated) -> Lambda -> Aurora, plus
a per-contract `/ask` endpoint that does the same retrieve-then-answer
pattern over that contract's own chunks.

## Why these choices

- **Aurora PostgreSQL Serverless v2 + pgvector**, not OpenSearch Serverless —
  one database instead of two systems, scales near-zero at low volume, and
  is single-tenant infrastructure you fully control (an easier story for a
  residency/compliance audit than a shared serverless control plane).
- **VPC endpoints only** for S3, Textract, Bedrock, Secrets Manager, and
  Step Functions — no NAT gateway, no internet egress. Contract text never
  leaves the AWS network.
- **Everything pinned to eu-west-2** — no cross-region replication, no
  default-region SDK calls. Bedrock model IDs are the `eu.*` cross-region
  inference profile where available so requests stay within Europe.
- **Customer-managed KMS key** (not AWS-managed) for S3, Aurora, Secrets
  Manager, and CloudWatch Logs — you control the key policy and rotation,
  and can produce it as evidence in an audit.
- **Cognito, admin-provisioned accounts only** — no public sign-up; MFA
  required. Procurement teams are added by an admin.
- **pg8000** (pure-Python Postgres driver) instead of psycopg2 — the
  Lambda dependency layer builds with a plain `pip install`, no
  compiled/platform-specific wheel to worry about.

## Repo layout

```
infra/terraform/     Terraform: networking, security (KMS), storage (S3),
                      database (Aurora+pgvector), pipeline (Lambdas +
                      Step Functions), auth (Cognito), api (API Gateway)
src/
  extraction/         Lambda: Textract -> text
  chunk_embed/        Lambda: chunk + embed -> pgvector
  field_extraction/   Lambda: retrieve + extract structured fields
  store_results/      Lambda: final write to the contracts table
  query_api/          Lambda: list/get/ask endpoints behind API Gateway
  common/             shared code (db, bedrock, chunking, prompts) —
                      packaged into the Lambda layer, not per-function zips
scripts/
  build_layer.sh   builds the shared dependency layer
  init_db.sql      one-time schema setup (pgvector, tables)
```

## Deploying

Prerequisites: an AWS account with Bedrock model access enabled in
`eu-west-2` for the models in `terraform.tfvars` (Bedrock model access is
opt-in per account/region — check the Bedrock console's "Model access"
page first), Terraform >= 1.7, Python 3.12, AWS CLI configured.

```bash
# 1. Build the Lambda dependency layer (pg8000 + shared common/ code)
./scripts/build_layer.sh

# 2. Configure and deploy the infrastructure
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars   # edit as needed
terraform init
terraform plan
terraform apply
```

### Database setup (one-time, after the first apply)

Aurora has no public endpoint by design. Connect via an SSM
port-forwarding session from a host inside the VPC (e.g. a temporary
bastion, or `aws ssm start-session` to any instance you place in the
private subnets), then:

```bash
psql "host=localhost port=5432 dbname=contracts user=cmt_admin sslmode=require" -f scripts/init_db.sql
```

Credentials are in Secrets Manager at the ARN in `terraform output db_secret_arn`.

### Uploading a contract

Upload under `raw/<category>/<vendor>/<filename>.pdf` in the raw bucket —
the category segment seeds the contract's category for filtering/display:

```bash
aws s3 cp my-contract.pdf \
  "s3://$(terraform -chdir=infra/terraform output -raw raw_contracts_bucket)/raw/software/acme-corp/my-contract.pdf"
```

The upload triggers the pipeline automatically (S3 -> EventBridge ->
Step Functions). Check progress in the Step Functions console, or query
the API once `status` reaches `complete`:

```bash
curl -H "Authorization: Bearer $ID_TOKEN" \
  "$(terraform -chdir=infra/terraform output -raw api_endpoint)/contracts"
```

## Frontend

A small React + Vite app in `frontend/` — sign in, browse contracts,
view extracted fields and risk flags, ask ad-hoc questions, and upload
new PDFs straight to S3. Terraform hosts the built app itself: a private
S3 bucket behind CloudFront (`infra/terraform/modules/frontend`), so
there's nothing extra to stand up.

Because the built app has to embed the API/Cognito IDs, and the API's
CORS policy has to know the frontend's CloudFront URL, this is a
two-pass deploy:

```bash
# 1. First apply - creates the API, Cognito, and an (empty) frontend
#    bucket/distribution so their outputs exist.
mkdir -p frontend/dist && touch frontend/dist/.keep   # placeholder so `apply` has something to upload
cd infra/terraform
terraform apply

# 2. Build the frontend against those outputs.
cd ../../frontend
npm install
cat > .env.production.local <<EOF
VITE_API_ENDPOINT=$(terraform -chdir=../infra/terraform output -raw api_endpoint)
VITE_AWS_REGION=eu-west-2
VITE_USER_POOL_ID=$(terraform -chdir=../infra/terraform output -raw cognito_user_pool_id)
VITE_USER_POOL_CLIENT_ID=$(terraform -chdir=../infra/terraform output -raw cognito_app_client_id)
EOF
npm run build

# 3. Second apply - uploads dist/ to S3 and invalidates the CloudFront cache.
cd ../infra/terraform
terraform apply
terraform output -raw frontend_url
```

Open the `frontend_url` output in a browser — that's the live app.
(`npm run dev` still works too, for local iteration against the same
deployed backend: `cp .env.example .env.local` with the same values
above, then `npm run dev` — `frontend_origins` in `terraform.tfvars`
already defaults to `http://localhost:5173` for this, and the deployed
CloudFront URL is added to CORS automatically.)

Cognito MFA is set to `OPTIONAL` (not `ON`) specifically so demo accounts
can sign in without a TOTP enrollment step the SPA doesn't implement —
turn it back to `ON` in `infra/terraform/modules/auth/main.tf` before
onboarding real users.

## Signing in (demo)

There's no public sign-up — Cognito is admin-provisioned only. Create a
demo login after the first `apply`:

```bash
./scripts/create_demo_user.sh you@example.com 'SomeStrongPassw0rd!'
```

This sets a *permanent* password (skips the forced first-login reset the
SPA doesn't implement), so you can sign in immediately at the frontend's
login form with that email/password. No MFA prompt, since MFA is
`OPTIONAL` for the demo pool.

## Demo data

Five real contracts from the public, CC-BY-licensed
[CUAD dataset](demo-data/README.md) are included under `demo-data/contracts/`.
Upload them and create a login in one go:

```bash
./scripts/load_demo_data.sh
./scripts/create_demo_user.sh you@example.com 'SomeStrongPassw0rd!'
```

Then open the frontend, sign in, and the five contracts will appear as
the pipeline finishes processing them (a minute or two each).

## What's intentionally left for you to fill in

- **Bedrock model access approval** — must be requested per-account
  per-region before the pipeline can invoke Claude/Titan.
- **Textract job polling** currently sleeps inside the `extraction`
  Lambda; for very large/slow scans, moving that to a native Step
  Functions wait/retry loop avoids tying up a Lambda invocation for the
  full OCR duration.
