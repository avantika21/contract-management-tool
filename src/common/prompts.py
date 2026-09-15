FIELD_EXTRACTION_SYSTEM_PROMPT = """You are a contract-review assistant for a procurement team.
You extract precise, literal facts from contract text - you do not
interpret, summarize, or add information that is not present. If a value
is not stated in the provided excerpts, use null. The excerpts are
numbered [1], [2], etc. - for every field you populate (not null), record
which excerpt number(s) support it in "field_citations", keyed by field
name, e.g. "field_citations": {"vendor_name": [1], "liability_cap_amount": [3]}.
Omit a field from "field_citations" if you left it null. Respond with ONLY
a single JSON object matching the requested schema, no prose, no markdown
fences."""

FIELD_EXTRACTION_SCHEMA = """{
  "vendor_name": string | null,
  "category": string | null,          // e.g. "software", "logistics", "professional_services"
  "effective_date": "YYYY-MM-DD" | null,
  "expiry_date": "YYYY-MM-DD" | null,
  "auto_renews": boolean | null,
  "renewal_notice_days": number | null,
  "termination_notice_days": number | null,
  "termination_for_convenience": boolean | null,
  "liability_cap_amount": number | null,
  "liability_cap_currency": string | null,   // ISO 4217, e.g. "GBP"
  "governing_law": string | null,

  "contract_value_amount": number | null,        // total contract value if stated
  "contract_value_currency": string | null,      // ISO 4217, e.g. "GBP"
  "payment_terms_days": number | null,           // e.g. 30 for "Net 30"
  "pricing_model": string | null,                // "fixed" | "time_and_materials" | "subscription" | "usage_based"
  "minimum_commitment": string | null,           // brief description of any minimum spend/volume commitment
  "price_escalation_clause": string | null,      // verbatim excerpt on price increases / CPI caps, else null

  "confidence_notes": string | null,         // brief note on any ambiguous or missing fields

  "field_citations": object                  // { "<field name>": [excerpt numbers] } for every populated field
}"""


def build_field_extraction_prompt(context_chunks: list[str]) -> str:
    context = "\n\n".join(f"[{i}] {chunk}" for i, chunk in enumerate(context_chunks, start=1))
    return f"""Extract the following fields from these contract excerpts.

Schema:
{FIELD_EXTRACTION_SCHEMA}

Contract excerpts:
{context}

Return only the JSON object. Populate "field_citations" with the excerpt
number(s) that support each non-null field."""


QA_SYSTEM_PROMPT = """You are a contract Q&A assistant for a procurement team.
Answer only using the provided, numbered contract excerpts. Every factual
claim in your answer must end with a bracketed citation to the excerpt
number(s) it comes from, e.g. "Payment is due within 30 days [2].". If the
excerpts do not contain the answer, say so explicitly rather than
guessing - do not cite an excerpt for a claim it does not support. Keep
answers concise."""


def build_qa_prompt(question: str, context_chunks: list[str]) -> str:
    context = "\n\n".join(f"[{i}] {chunk}" for i, chunk in enumerate(context_chunks, start=1))
    return f"""Contract excerpts:
{context}

Question: {question}

Answer based only on the excerpts above. Cite each claim with the
bracketed excerpt number(s) it is drawn from, e.g. [1] or [2][3]."""
