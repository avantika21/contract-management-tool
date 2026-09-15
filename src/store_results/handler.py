"""Step 5: write the final structured record to the contracts table so it's
instantly searchable instead of buried in a PDF.
"""
import json

from common.db import get_connection


def handler(event, context):
    contract_id = event["contract_id"]
    fields = event.get("extracted_fields", {}) or {}
    extraction_sources = event.get("extraction_sources") or {"citations": {}, "excerpts": []}

    conn = get_connection()
    try:
        conn.run(
            """
            UPDATE contracts SET
                vendor_name = :vendor_name,
                category = COALESCE(:category, category),
                effective_date = :effective_date,
                expiry_date = :expiry_date,
                auto_renews = :auto_renews,
                renewal_notice_days = :renewal_notice_days,
                termination_notice_days = :termination_notice_days,
                termination_for_convenience = :termination_for_convenience,
                liability_cap_amount = :liability_cap_amount,
                liability_cap_currency = :liability_cap_currency,
                governing_law = :governing_law,
                data_residency_clause = :data_residency_clause,
                contract_value_amount = :contract_value_amount,
                contract_value_currency = :contract_value_currency,
                payment_terms_days = :payment_terms_days,
                pricing_model = :pricing_model,
                minimum_commitment = :minimum_commitment,
                price_escalation_clause = :price_escalation_clause,
                extracted_fields = CAST(:extracted_fields_json AS jsonb),
                extraction_sources = CAST(:extraction_sources_json AS jsonb),
                status = 'complete',
                updated_at = now()
            WHERE id = :contract_id
            """,
            contract_id=contract_id,
            vendor_name=fields.get("vendor_name"),
            category=fields.get("category"),
            effective_date=fields.get("effective_date"),
            expiry_date=fields.get("expiry_date"),
            auto_renews=fields.get("auto_renews"),
            renewal_notice_days=fields.get("renewal_notice_days"),
            termination_notice_days=fields.get("termination_notice_days"),
            termination_for_convenience=fields.get("termination_for_convenience"),
            liability_cap_amount=fields.get("liability_cap_amount"),
            liability_cap_currency=fields.get("liability_cap_currency"),
            governing_law=fields.get("governing_law"),
            data_residency_clause=fields.get("data_residency_clause"),
            contract_value_amount=fields.get("contract_value_amount"),
            contract_value_currency=fields.get("contract_value_currency"),
            payment_terms_days=fields.get("payment_terms_days"),
            pricing_model=fields.get("pricing_model"),
            minimum_commitment=fields.get("minimum_commitment"),
            price_escalation_clause=fields.get("price_escalation_clause"),
            extracted_fields_json=json.dumps(fields),
            extraction_sources_json=json.dumps(extraction_sources),
        )
    finally:
        conn.close()

    return {"contract_id": contract_id, "status": "complete"}
