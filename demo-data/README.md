# Demo data

## Contracts (`contracts/`)

Ten **synthetic** contracts (not real filings), two per category matching
the upload form's category list (`supply`, `service`, `maintenance`,
`outsourcing`, `hosting`). Each is written to populate every field in the
extraction schema (`src/common/prompts.py::FIELD_EXTRACTION_SCHEMA`) with
a clean, unambiguous value - concrete dates, a real liability cap amount,
an SLA/service-credit table, price escalation, insurance limits, etc. -
and uses numbered section headings (`N. TITLE` / `N.N Sub-clause`) that
line up with the clause-aware chunker (`src/common/chunking.py`) so each
clause retrieves as its own chunk.

An earlier version of this demo set used real CUAD-sourced SEC filings
(see "Why not real filings?" below); those are gone now in favor of this
purpose-built set, which is more reliable for demos since every field
comes back populated rather than `null` behind a `[***]` redaction.

| File | Category | Vendor / counterparty | Notes |
|---|---|---|---|
| `hosting__northbridge-data-systems__cloud-hosting-agreement.pdf` | hosting | Northbridge Data Systems Ltd &rarr; Solstice Retail Group plc | GBP; auto-renews; renewal action date lands inside the 90-day lookahead as of late 2026 |
| `hosting__vantage-cloud-systems__cloud-hosting-agreement.pdf` | hosting | Vantage Cloud Systems Inc. &rarr; Harlow Fitness Holdings, Inc. | USD; does **not** auto-renew; already past its expiry/action date as of late 2026 - shows as "Overdue" |
| `supply__meridian-components__component-supply-agreement.pdf` | supply | Meridian Components Ltd &rarr; Solaris Robotics Inc. | USD; exclusive supply; renewal action date is only days away as of late 2026 |
| `supply__atlas-packaging-materials__packaging-supply-agreement.pdf` | supply | Atlas Packaging Materials GmbH &rarr; Kestrel Foods plc | EUR; no termination for convenience (fixed term only); renewal far out |
| `service__cascade-analytics-partners__data-analytics-services-agreement.pdf` | service | Cascade Analytics Partners LLC &rarr; Harrow & Vance LLP | USD; time-and-materials pricing; renewal action date inside the 90-day lookahead |
| `service__beacon-security-consulting__penetration-testing-services-agreement.pdf` | service | Beacon Security Consulting Ltd &rarr; Whitfield & Cole Insurance plc | GBP; exclusive; unlimited liability carve-out for confidentiality breach; renewal far out |
| `maintenance__ferro-industrial-maintenance__equipment-maintenance-agreement.pdf` | maintenance | Ferro Industrial Maintenance Services LLC &rarr; Bramwell Steelworks Inc. | USD; fixed term, no auto-renewal; already past its action date as of late 2026 - shows as "Overdue" |
| `maintenance__pinnacle-it-support-group__it-support-and-maintenance-agreement.pdf` | maintenance | Pinnacle IT Support Group Ltd &rarr; Thornfield Legal Services LLP | GBP; per-device subscription; renewal far out |
| `outsourcing__meritus-bpo-solutions__claims-processing-outsourcing-agreement.pdf` | outsourcing | Meritus BPO Solutions Pvt Ltd &rarr; Coastal Home Insurance Co. | USD; usage-based pricing; exclusive; renewal action date is only days away as of late 2026 |
| `outsourcing__vertex-manufacturing-outsource-partners__assembly-outsourcing-agreement.pdf` | outsourcing | Vertex Manufacturing Outsource Partners Ltd &rarr; Solent Audio Equipment Ltd | GBP; renewal far out |

Six of the ten fall inside the dashboard's 90-day "renewals needing
action" lookahead as of late 2026 (two already overdue, four upcoming);
the other four are further out and read as healthy. Currencies, governing
law, pricing models (fixed / subscription / time-and-materials /
usage-based), and auto-renewal terms are deliberately varied across the
set so list/filter views and the value-breakdown stat show a realistic mix
rather than ten near-identical contracts.

Filenames follow `<category>__<vendor-slug>__<description>.pdf`, matched
by `scripts/load_demo_data.sh` to build the `raw/<category>/<vendor>/...`
S3 key the pipeline expects.

### Regenerating

`hosting__northbridge-data-systems__cloud-hosting-agreement.pdf` was
authored by hand; the other nine are produced by
`scripts/generate_demo_contracts.py` (`pip install reportlab` first). Edit
the contract specs in that script and re-run it to change wording, dates,
or amounts - don't hand-edit the generated PDFs.

### Why not real filings?

An earlier version of this set used five contracts pulled from the
[Contract Understanding Atticus Dataset (CUAD) v1](https://www.atticusprojectai.org/cuad)
(CC BY 4.0) - genuine SEC-filed exhibits, good for showing OCR/citation
quality on real documents. In practice they were a poor fit for a *demo*:
CUAD's commercial terms (dollar amounts, percentages, day counts) are
frequently redacted as `[***]` for confidentiality, one was a template
with the seller name and dates left blank, and none of the five populated
every field in the schema. That tradeoff (realism vs. every field working)
is why this set switched to purpose-built synthetic contracts instead.
