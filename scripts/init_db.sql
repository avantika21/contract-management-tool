-- Run once against the Aurora cluster after `terraform apply`.
-- Connect via an SSH/SSM tunnel or a bastion in the VPC - the cluster has
-- no public endpoint. See README.md "Database setup".

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- for gen_random_uuid()

CREATE TABLE IF NOT EXISTS contracts (
    id                            UUID PRIMARY KEY,
    s3_key                        TEXT NOT NULL,
    vendor_name                   TEXT,
    category                      TEXT,
    status                        TEXT NOT NULL DEFAULT 'processing', -- processing | complete | failed
    effective_date                DATE,
    expiry_date                   DATE,
    auto_renews                   BOOLEAN,
    renewal_notice_days           INTEGER,
    termination_notice_days       INTEGER,
    termination_for_convenience   BOOLEAN,
    liability_cap_amount          NUMERIC,
    liability_cap_currency        TEXT,
    governing_law                 TEXT,
    data_residency_clause         TEXT,
    contract_value_amount         NUMERIC,
    contract_value_currency       TEXT,
    payment_terms_days            INTEGER,
    pricing_model                 TEXT,
    minimum_commitment            TEXT,
    price_escalation_clause       TEXT,
    sla_summary                   TEXT,
    exclusivity_clause            TEXT,
    change_of_control_clause      TEXT,
    insurance_requirements        TEXT,
    indemnification_summary       TEXT,
    extracted_fields              JSONB,
    created_at                    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Safe to re-run against a cluster that already has the contracts table
-- from before these columns existed (CREATE TABLE IF NOT EXISTS above is a
-- no-op in that case, so the new columns need adding explicitly).
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS contract_value_amount NUMERIC;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS contract_value_currency TEXT;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS payment_terms_days INTEGER;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS pricing_model TEXT;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS minimum_commitment TEXT;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS price_escalation_clause TEXT;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS sla_summary TEXT;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS exclusivity_clause TEXT;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS change_of_control_clause TEXT;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS insurance_requirements TEXT;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS indemnification_summary TEXT;
-- { "citations": {"<field name>": [excerpt numbers]}, "excerpts": [{ref, chunk_index, content}] }
-- so each extracted field can be traced back to the exact contract_chunks row it came from.
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS extraction_sources JSONB;

-- Drops the risk-comparison columns/index for a cluster that already has
-- them from before the compare_reference step was removed.
DROP INDEX IF EXISTS idx_contracts_risk_score;
ALTER TABLE contracts DROP COLUMN IF EXISTS risk_flags;
ALTER TABLE contracts DROP COLUMN IF EXISTS risk_score;

CREATE INDEX IF NOT EXISTS idx_contracts_category ON contracts (category);
CREATE INDEX IF NOT EXISTS idx_contracts_expiry ON contracts (expiry_date);
CREATE INDEX IF NOT EXISTS idx_contracts_value ON contracts (contract_value_amount);

CREATE TABLE IF NOT EXISTS contract_chunks (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id   UUID NOT NULL REFERENCES contracts (id) ON DELETE CASCADE,
    chunk_index   INTEGER NOT NULL,
    content       TEXT NOT NULL,
    embedding     VECTOR(1024) NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_contract_chunks_contract_id ON contract_chunks (contract_id);
CREATE INDEX IF NOT EXISTS idx_contract_chunks_embedding
    ON contract_chunks USING hnsw (embedding vector_cosine_ops);

-- Keyword leg of hybrid (vector + keyword) chunk retrieval - see
-- src/common/retrieval.py. Generated column so it stays in sync with
-- `content` automatically and can't drift out of date.
ALTER TABLE contract_chunks ADD COLUMN IF NOT EXISTS content_tsv tsvector
    GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;
CREATE INDEX IF NOT EXISTS idx_contract_chunks_content_tsv ON contract_chunks USING gin (content_tsv);

-- Drops the reference-contract table for a cluster that already has it
-- from before the compare_reference (risk-comparison) step was removed.
DROP TABLE IF EXISTS reference_contracts;
