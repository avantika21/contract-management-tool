#!/usr/bin/env python3
"""One-off generator for the synthetic demo contracts under demo-data/contracts/.

Not part of the application or its Lambda layer - run manually, locally,
whenever the demo contract set needs to change:

    pip install reportlab
    python3 scripts/generate_demo_contracts.py

Each contract is a plain-language agreement written to populate every
field in the extraction schema (src/common/prompts.py::FIELD_EXTRACTION_SCHEMA)
with a clean, unambiguous value, using section numbering (N. TITLE /
N.N Sub-clause) that lines up with the clause-aware chunker
(src/common/chunking.py) so each clause retrieves as its own chunk.
"""
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "demo-data", "contracts")

_styles = getSampleStyleSheet()
TITLE = ParagraphStyle("ContractTitle", parent=_styles["Title"], fontSize=15, leading=19, alignment=TA_CENTER)
PARTIES = ParagraphStyle("Parties", parent=_styles["Normal"], fontSize=10.5, leading=14, alignment=TA_CENTER, spaceAfter=4)
BODY = ParagraphStyle("Body", parent=_styles["Normal"], fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=8)
HEADING = ParagraphStyle("SectionHeading", parent=_styles["Normal"], fontSize=11, leading=14, spaceBefore=10, spaceAfter=6, fontName="Helvetica-Bold")
SIGLABEL = ParagraphStyle("SigLabel", parent=_styles["Normal"], fontSize=10, leading=13, spaceBefore=2)


def _doc(vendor_block: str, client_block: str, title: str) -> list:
    return [
        Paragraph(title, TITLE),
        Spacer(1, 4),
        Paragraph("between", PARTIES),
        Paragraph(f"<b>{vendor_block}</b>", PARTIES),
        Paragraph("and", PARTIES),
        Paragraph(f"<b>{client_block}</b>", PARTIES),
        Spacer(1, 10),
    ]


def _sections(sections: list[tuple[str, list[str]]]) -> list:
    flow = []
    for heading, paragraphs in sections:
        flow.append(Paragraph(heading, HEADING))
        for p in paragraphs:
            flow.append(Paragraph(p, BODY))
    return flow


def _sla_table(header: list[str], rows: list[list[str]]) -> Table:
    data = [header] + rows
    t = Table(data, hAlign="LEFT", colWidths=[2.6 * inch, 3.4 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return t


def _signature_block(vendor_name: str, vendor_signee: str, vendor_title: str, client_name: str, client_signee: str, client_title: str, date_str: str) -> list:
    return [
        Spacer(1, 14),
        Paragraph("IN WITNESS WHEREOF, the Parties have executed this Agreement as of the Effective Date.", BODY),
        Spacer(1, 20),
        Table(
            [
                [Paragraph(f"For and on behalf of<br/><b>{vendor_name.upper()}</b>", SIGLABEL),
                 Paragraph(f"For and on behalf of<br/><b>{client_name.upper()}</b>", SIGLABEL)],
                [Paragraph("Signature: ____________________________", SIGLABEL),
                 Paragraph("Signature: ____________________________", SIGLABEL)],
                [Paragraph(f"Name: {vendor_signee}", SIGLABEL), Paragraph(f"Name: {client_signee}", SIGLABEL)],
                [Paragraph(f"Title: {vendor_title}", SIGLABEL), Paragraph(f"Title: {client_title}", SIGLABEL)],
                [Paragraph(f"Date: {date_str}", SIGLABEL), Paragraph(f"Date: {date_str}", SIGLABEL)],
            ],
            colWidths=[3 * inch, 3 * inch],
            hAlign="LEFT",
        ),
    ]


def build(filename: str, title: str, vendor_block: str, client_block: str, intro: list[str], sections: list, sig: dict, tables: dict | None = None):
    """`tables` maps a section heading to an _sla_table() to insert right
    after that heading's paragraphs."""
    tables = tables or {}
    path = os.path.join(OUT_DIR, filename)
    doc = SimpleDocTemplate(
        path, pagesize=LETTER,
        topMargin=0.85 * inch, bottomMargin=0.85 * inch,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
    )
    flow = _doc(vendor_block, client_block, title)
    for p in intro:
        flow.append(Paragraph(p, BODY))
    for heading, paragraphs in sections:
        flow.append(Paragraph(heading, HEADING))
        for p in paragraphs:
            flow.append(Paragraph(p, BODY))
        if heading in tables:
            flow.append(tables[heading])
            flow.append(Spacer(1, 8))
    flow.extend(_signature_block(**sig))
    doc.build(flow)
    print(f"wrote {path}")


# ---------------------------------------------------------------------------
# 1. HOSTING - Vantage Cloud Systems Inc. / Harlow Fitness Holdings, Inc.
# ---------------------------------------------------------------------------
build(
    filename="hosting__vantage-cloud-systems__cloud-hosting-agreement.pdf",
    title="MASTER CLOUD HOSTING AGREEMENT",
    vendor_block="Vantage Cloud Systems Inc. (&ldquo;Vendor&rdquo;)",
    client_block="Harlow Fitness Holdings, Inc. (&ldquo;Customer&rdquo;)",
    intro=[
        "This Master Cloud Hosting Agreement (this &ldquo;Agreement&rdquo;) is entered into and effective as of "
        "September 1, 2023 (the &ldquo;Effective Date&rdquo;) by and between Vantage Cloud Systems Inc., a Delaware "
        "corporation with its principal place of business at 400 Market Street, Wilmington, Delaware 19801 "
        "(&ldquo;Vendor&rdquo;), and Harlow Fitness Holdings, Inc., a Delaware corporation with its principal place "
        "of business at 88 Commerce Way, Austin, Texas 78701 (&ldquo;Customer&rdquo;), each a &ldquo;Party&rdquo; "
        "and together the &ldquo;Parties.&rdquo;",
        "RECITALS. Vendor operates a cloud infrastructure platform used to host web applications, and Customer "
        "wishes to host its member-facing fitness applications on that platform on the terms below.",
    ],
    sections=[
        ("1. TERM AND RENEWAL", [
            "1.1 Initial Term. This Agreement commences on the Effective Date and continues for an initial term "
            "of three (3) years, expiring on August 31, 2026 (the &ldquo;Initial Term&rdquo;), unless terminated "
            "earlier under Section 9.",
            "1.2 Renewal. This Agreement does not renew automatically. At least sixty (60) days before the end of "
            "the Initial Term, the Parties shall discuss in good faith whether to enter into a new term on "
            "mutually agreed terms; absent a signed renewal, this Agreement expires at the end of the Initial Term.",
        ]),
        ("2. SERVICES; MINIMUM COMMITMENT", [
            "2.1 Vendor shall provide cloud hosting, storage, and infrastructure-monitoring services as described "
            "in the applicable order form (the &ldquo;Services&rdquo;).",
            "2.2 Minimum Commitment. Customer commits to a minimum of two hundred (200) active user seats for "
            "each year of the Term, billed whether or not actually used (the &ldquo;Minimum Commitment&rdquo;).",
        ]),
        ("3. FEES AND PAYMENT", [
            "3.1 Fees. Customer shall pay Vendor an annual subscription fee of one hundred twenty thousand "
            "dollars ($120,000), invoiced annually in advance. The aggregate value of this Agreement over the "
            "three (3)-year Initial Term is three hundred sixty thousand dollars ($360,000).",
            "3.2 Payment Terms. Customer shall pay each undisputed invoice within thirty (30) days of the "
            "invoice date.",
            "3.3 Pricing Model. The Services are provided on a subscription basis, priced per active user seat.",
            "3.4 Price Escalation. At each renewal, the annual subscription fee may increase by up to the "
            "percentage increase in the U.S. Consumer Price Index (CPI-U) over the preceding twelve (12) months, "
            "capped at four percent (4%) per year.",
        ]),
        ("4. SERVICE LEVELS", [
            "4.1 Vendor shall use commercially reasonable efforts to achieve monthly Service uptime of at least "
            "99.5%, measured as described in the order form.",
            "4.2 If actual monthly uptime falls below 99.5%, Customer shall receive a service credit against "
            "the next invoice equal to 5% of that month's fees for each full percentage point of shortfall, "
            "up to a maximum of 20% of that month's fees.",
        ]),
        ("5. DATA RESIDENCY AND SECURITY", [
            "5.1 Data Residency. All Customer data shall be stored and processed exclusively within data centers "
            "located in the United States. Vendor shall not replicate or process Customer data outside the "
            "United States without Customer's prior written consent.",
        ]),
        ("6. LIMITATION OF LIABILITY", [
            "6.1 Except for liabilities arising from a Party's breach of confidentiality or indemnification "
            "obligations, each Party's total aggregate liability arising out of this Agreement shall not exceed "
            "five hundred thousand dollars ($500,000).",
            "6.2 Neither Party shall be liable for indirect, special, or consequential damages.",
        ]),
        ("7. INDEMNIFICATION", [
            "7.1 Vendor shall defend, indemnify, and hold harmless Customer from third-party claims arising out "
            "of (a) Vendor's breach of this Agreement, or (b) infringement of a third party's intellectual "
            "property rights by the Services.",
        ]),
        ("8. INSURANCE", [
            "8.1 Throughout the Term, Vendor shall maintain Commercial General Liability insurance of not less "
            "than $1,000,000 per occurrence, Professional Liability insurance of not less than $1,000,000 per "
            "claim, and Cyber Liability insurance of not less than $3,000,000 per occurrence.",
        ]),
        ("9. TERMINATION", [
            "9.1 Termination for Cause. Either Party may terminate this Agreement immediately upon written notice "
            "if the other Party commits a material breach and fails to cure it within thirty (30) days of notice.",
            "9.2 Termination for Convenience. Either Party may terminate this Agreement for convenience by giving "
            "the other Party not less than ninety (90) days' prior written notice.",
        ]),
        ("10. CHANGE OF CONTROL; ASSIGNMENT", [
            "10.1 Neither Party may assign this Agreement without the other Party's prior written consent, "
            "except in connection with a merger, acquisition, or sale of substantially all of its assets.",
            "10.2 If a Party undergoes a Change of Control involving a direct competitor of the other Party, "
            "the other Party may terminate this Agreement on thirty (30) days' written notice given within "
            "ninety (90) days of becoming aware of the Change of Control.",
        ]),
        ("11. GOVERNING LAW", [
            "11.1 This Agreement is governed by, and shall be construed in accordance with, the laws of the "
            "State of Delaware, without regard to its conflict-of-laws principles. The state and federal courts "
            "located in Delaware shall have exclusive jurisdiction over any dispute arising out of this Agreement.",
        ]),
        ("12. GENERAL PROVISIONS", [
            "12.1 Entire Agreement. This Agreement constitutes the entire agreement between the Parties with "
            "respect to its subject matter.",
            "12.2 Notices. All notices shall be in writing and delivered to the addresses set out above.",
        ]),
    ],
    tables={
        "4. SERVICE LEVELS": _sla_table(
            ["Monthly uptime achieved", "Service credit"],
            [["99.0% - 99.49%", "5% of that month's fees"],
             ["95.0% - 98.99%", "10% of that month's fees"],
             ["Below 95.0%", "20% of that month's fees"]],
        )
    },
    sig=dict(
        vendor_name="Vantage Cloud Systems Inc.", vendor_signee="Rachel Kim", vendor_title="VP, Customer Success",
        client_name="Harlow Fitness Holdings, Inc.", client_signee="Marcus Dell", client_title="Chief Operating Officer",
        date_str="September 1, 2023",
    ),
)

# ---------------------------------------------------------------------------
# 2. SUPPLY - Meridian Components Ltd / Solaris Robotics Inc.
# ---------------------------------------------------------------------------
build(
    filename="supply__meridian-components__component-supply-agreement.pdf",
    title="COMPONENT SUPPLY AGREEMENT",
    vendor_block="Meridian Components Ltd (&ldquo;Seller&rdquo;)",
    client_block="Solaris Robotics Inc. (&ldquo;Buyer&rdquo;)",
    intro=[
        "This Component Supply Agreement (this &ldquo;Agreement&rdquo;) is entered into and effective as of "
        "October 20, 2024 (the &ldquo;Effective Date&rdquo;) by and between Meridian Components Ltd, a company "
        "registered in England and Wales with its registered office at 14 Ironbridge Road, Birmingham, B4 6AA, "
        "United Kingdom (&ldquo;Seller&rdquo;), and Solaris Robotics Inc., a Delaware corporation with its "
        "principal place of business at 900 Innovation Drive, San Jose, California 95110 (&ldquo;Buyer&rdquo;), "
        "each a &ldquo;Party&rdquo; and together the &ldquo;Parties.&rdquo;",
        "RECITALS. Seller manufactures precision electromechanical components, and Buyer wishes to purchase such "
        "components for use in its robotics products on the terms below.",
    ],
    sections=[
        ("1. TERM AND RENEWAL", [
            "1.1 Initial Term. This Agreement commences on the Effective Date and continues for an initial term "
            "of two (2) years, expiring on October 20, 2026 (the &ldquo;Initial Term&rdquo;), unless terminated "
            "earlier under Section 9.",
            "1.2 Automatic Renewal. Upon expiry of the Initial Term, this Agreement automatically renews for "
            "successive one (1)-year periods (each, a &ldquo;Renewal Term&rdquo;), unless either Party gives the "
            "other written notice of non-renewal at least thirty (30) days before the end of the then-current term.",
        ]),
        ("2. EXCLUSIVITY; MINIMUM COMMITMENT", [
            "2.1 Exclusivity. During the Term, Buyer shall purchase one hundred percent (100%) of its requirement "
            "for the components listed in Schedule A exclusively from Seller, and Seller shall not supply "
            "materially similar components to any direct competitor of Buyer named in Schedule B.",
            "2.2 Minimum Commitment. Buyer commits to a minimum annual purchase volume of one million dollars "
            "($1,000,000) in components for each year of the Term (the &ldquo;Minimum Commitment&rdquo;).",
        ]),
        ("3. PRICING AND PAYMENT", [
            "3.1 Fees. Unit prices are fixed as set out in Schedule A. Based on Buyer's forecast order volumes, "
            "the aggregate value of this Agreement over the two (2)-year Initial Term is estimated at two million "
            "four hundred thousand dollars ($2,400,000).",
            "3.2 Payment Terms. Buyer shall pay each undisputed invoice within forty-five (45) days of the "
            "invoice date.",
            "3.3 Pricing Model. Components are sold at fixed unit prices per Schedule A, applied to each "
            "purchase order.",
            "3.4 Price Escalation. Seller may increase unit prices once per calendar year by the lesser of (i) "
            "six percent (6%), or (ii) the percentage increase in the LME Copper Index over the preceding twelve "
            "(12) months.",
        ]),
        ("4. DELIVERY PERFORMANCE", [
            "4.1 Seller shall use commercially reasonable efforts to achieve an on-time delivery rate of at "
            "least ninety-five percent (95%) and a defect rate below one percent (1%), each measured quarterly.",
            "4.2 If Seller's on-time delivery rate falls below 95% in a given quarter, Buyer shall be entitled "
            "to a service credit of 3% of that quarter's fees for each full percentage point of shortfall, up "
            "to a maximum of 15% of that quarter's fees.",
        ]),
        ("5. LIMITATION OF LIABILITY", [
            "5.1 Except for liabilities arising from a Party's breach of confidentiality, IP infringement, or "
            "indemnification obligations, each Party's total aggregate liability arising out of this Agreement "
            "shall not exceed two million dollars ($2,000,000).",
        ]),
        ("6. INDEMNIFICATION", [
            "6.1 Seller shall defend, indemnify, and hold harmless Buyer from third-party claims arising out of "
            "(a) defective components, or (b) infringement of a third party's intellectual property rights by "
            "the components.",
        ]),
        ("7. INSURANCE", [
            "7.1 Throughout the Term, Seller shall maintain Product Liability insurance of not less than "
            "$5,000,000 per occurrence and Commercial General Liability insurance of not less than $2,000,000 "
            "per occurrence.",
        ]),
        ("8. TERMINATION", [
            "8.1 Termination for Cause. Either Party may terminate this Agreement immediately upon written notice "
            "if the other Party commits a material breach and fails to cure it within thirty (30) days of notice.",
            "8.2 Termination for Convenience. Either Party may terminate this Agreement for convenience by giving "
            "the other Party not less than ninety (90) days' prior written notice.",
        ]),
        ("9. CHANGE OF CONTROL; ASSIGNMENT", [
            "9.1 Neither Party may assign this Agreement without the other Party's prior written consent, except "
            "in connection with a merger, acquisition, or sale of substantially all of its assets.",
        ]),
        ("10. GOVERNING LAW", [
            "10.1 This Agreement is governed by, and shall be construed in accordance with, the laws of the "
            "State of New York, without regard to its conflict-of-laws principles. The state and federal courts "
            "located in New York County, New York shall have exclusive jurisdiction over any dispute arising "
            "out of this Agreement.",
        ]),
        ("11. GENERAL PROVISIONS", [
            "11.1 Entire Agreement. This Agreement, together with its Schedules, constitutes the entire "
            "agreement between the Parties with respect to its subject matter.",
        ]),
    ],
    sig=dict(
        vendor_name="Meridian Components Ltd", vendor_signee="Owen Faraday", vendor_title="Commercial Director",
        client_name="Solaris Robotics Inc.", client_signee="Priya Nathan", client_title="VP, Supply Chain",
        date_str="October 20, 2024",
    ),
)

# ---------------------------------------------------------------------------
# 3. SUPPLY - Atlas Packaging Materials GmbH / Kestrel Foods plc
# ---------------------------------------------------------------------------
build(
    filename="supply__atlas-packaging-materials__packaging-supply-agreement.pdf",
    title="PACKAGING MATERIALS SUPPLY AGREEMENT",
    vendor_block="Atlas Packaging Materials GmbH (&ldquo;Supplier&rdquo;)",
    client_block="Kestrel Foods plc (&ldquo;Buyer&rdquo;)",
    intro=[
        "This Packaging Materials Supply Agreement (this &ldquo;Agreement&rdquo;) is entered into and effective "
        "as of January 15, 2025 (the &ldquo;Effective Date&rdquo;) by and between Atlas Packaging Materials GmbH, "
        "a company organized under the laws of the Federal Republic of Germany with its registered office at "
        "Industriestra&szlig;e 22, 51063 Cologne, Germany (&ldquo;Supplier&rdquo;), and Kestrel Foods plc, a "
        "company registered in England and Wales with its registered office at 7 Orchard Court, Bristol, BS1 "
        "4ST, United Kingdom (&ldquo;Buyer&rdquo;), each a &ldquo;Party&rdquo; and together the &ldquo;Parties.&rdquo;",
        "RECITALS. Supplier manufactures food-grade packaging materials, and Buyer wishes to purchase such "
        "materials for its food production lines on the terms below.",
    ],
    sections=[
        ("1. TERM AND RENEWAL", [
            "1.1 Initial Term. This Agreement commences on the Effective Date and continues for an initial term "
            "of three (3) years, expiring on January 14, 2028 (the &ldquo;Initial Term&rdquo;), unless terminated "
            "earlier under Section 9.",
            "1.2 Automatic Renewal. Upon expiry of the Initial Term, this Agreement automatically renews for "
            "successive two (2)-year periods, unless either Party gives the other written notice of non-renewal "
            "at least sixty (60) days before the end of the then-current term.",
        ]),
        ("2. MINIMUM COMMITMENT", [
            "2.1 Buyer commits to a minimum annual purchase volume of one million (1,000,000) units of packaging "
            "materials for each year of the Term. If Buyer orders fewer units in a given year, Buyer shall pay "
            "Supplier a shortfall fee equal to fifty percent (50%) of the unordered portion of the Minimum "
            "Commitment.",
        ]),
        ("3. PRICING AND PAYMENT", [
            "3.1 Fees. Unit prices are fixed as set out in Schedule A. Based on the Minimum Commitment, the "
            "aggregate value of this Agreement over the three (3)-year Initial Term is estimated at five million "
            "four hundred thousand euros (&euro;5,400,000).",
            "3.2 Payment Terms. Buyer shall pay each undisputed invoice within sixty (60) days of the invoice date.",
            "3.3 Pricing Model. Materials are sold at fixed unit prices per Schedule A.",
            "3.4 Price Escalation. Unit prices are adjusted annually on each anniversary of the Effective Date "
            "in line with the Eurozone Harmonised Index of Consumer Prices (HICP), capped at five percent (5%) "
            "per year.",
        ]),
        ("4. DELIVERY PERFORMANCE", [
            "4.1 Supplier shall use commercially reasonable efforts to achieve an on-time delivery rate of at "
            "least ninety-seven percent (97%), measured quarterly.",
            "4.2 For each week a shipment is late, Buyer shall be entitled to a service credit of two percent "
            "(2%) of that shipment's value, up to a maximum of fifteen percent (15%) of the shipment's value.",
        ]),
        ("5. LIMITATION OF LIABILITY", [
            "5.1 Except for liabilities arising from a Party's breach of confidentiality, IP infringement, or "
            "indemnification obligations, each Party's total aggregate liability arising out of this Agreement "
            "shall not exceed one million five hundred thousand euros (&euro;1,500,000).",
        ]),
        ("6. INDEMNIFICATION", [
            "6.1 Supplier shall defend, indemnify, and hold harmless Buyer from third-party claims arising out "
            "of (a) defective or non-conforming materials, or (b) infringement of a third party's intellectual "
            "property rights by the materials.",
        ]),
        ("7. INSURANCE", [
            "7.1 Throughout the Term, Supplier shall maintain Product Liability insurance of not less than "
            "&euro;3,000,000 per occurrence and Commercial General Liability insurance of not less than "
            "&euro;1,000,000 per occurrence.",
        ]),
        ("8. TERMINATION", [
            "8.1 Termination for Cause. Either Party may terminate this Agreement immediately upon written "
            "notice if the other Party commits a material breach and fails to cure it within thirty (30) days "
            "of notice. There is no right to terminate this Agreement for convenience prior to expiry of the "
            "then-current term.",
        ]),
        ("9. CHANGE OF CONTROL; ASSIGNMENT", [
            "9.1 Neither Party may assign this Agreement without the other Party's prior written consent, "
            "except in connection with a merger, acquisition, or sale of substantially all of its assets.",
        ]),
        ("10. GOVERNING LAW", [
            "10.1 This Agreement is governed by, and shall be construed in accordance with, the laws of the "
            "Federal Republic of Germany. The courts of Cologne, Germany shall have exclusive jurisdiction over "
            "any dispute arising out of this Agreement.",
        ]),
        ("11. GENERAL PROVISIONS", [
            "11.1 Entire Agreement. This Agreement, together with its Schedules, constitutes the entire "
            "agreement between the Parties with respect to its subject matter.",
        ]),
    ],
    sig=dict(
        vendor_name="Atlas Packaging Materials GmbH", vendor_signee="Lena Brandt", vendor_title="Head of Commercial",
        client_name="Kestrel Foods plc", client_signee="Ian Postlethwaite", client_title="Procurement Director",
        date_str="January 15, 2025",
    ),
)

# ---------------------------------------------------------------------------
# 4. SERVICE - Cascade Analytics Partners LLC / Harrow & Vance LLP
# ---------------------------------------------------------------------------
build(
    filename="service__cascade-analytics-partners__data-analytics-services-agreement.pdf",
    title="DATA ANALYTICS SERVICES AGREEMENT",
    vendor_block="Cascade Analytics Partners LLC (&ldquo;Consultant&rdquo;)",
    client_block="Harrow &amp; Vance LLP (&ldquo;Client&rdquo;)",
    intro=[
        "This Data Analytics Services Agreement (this &ldquo;Agreement&rdquo;) is entered into and effective as "
        "of December 1, 2024 (the &ldquo;Effective Date&rdquo;) by and between Cascade Analytics Partners LLC, a "
        "California limited liability company with its principal place of business at 55 Bayview Terrace, San "
        "Francisco, California 94105 (&ldquo;Consultant&rdquo;), and Harrow &amp; Vance LLP, a limited liability "
        "partnership with its principal place of business at 200 Legal Plaza, Chicago, Illinois 60601 "
        "(&ldquo;Client&rdquo;), each a &ldquo;Party&rdquo; and together the &ldquo;Parties.&rdquo;",
        "RECITALS. Consultant provides data analytics consulting services, and Client wishes to engage Consultant "
        "to analyze case-management data on the terms below.",
    ],
    sections=[
        ("1. TERM AND RENEWAL", [
            "1.1 Initial Term. This Agreement commences on the Effective Date and continues for an initial term "
            "of two (2) years, expiring on December 1, 2026 (the &ldquo;Initial Term&rdquo;), unless terminated "
            "earlier under Section 9.",
            "1.2 Automatic Renewal. Upon expiry of the Initial Term, this Agreement automatically renews for "
            "successive one (1)-year periods, unless either Party gives the other written notice of non-renewal "
            "at least forty-five (45) days before the end of the then-current term.",
        ]),
        ("2. SERVICES; MINIMUM COMMITMENT", [
            "2.1 Consultant shall provide data analytics, dashboarding, and reporting services as described in "
            "the applicable statement of work (the &ldquo;Services&rdquo;), billed on a time-and-materials basis "
            "at the hourly rates set out in Schedule A.",
            "2.2 Minimum Commitment. Client commits to a minimum of one thousand (1,000) consulting hours per "
            "year; if Client's actual usage in a year falls below this minimum, Client shall pay Consultant for "
            "the shortfall at the applicable hourly rate.",
        ]),
        ("3. FEES AND PAYMENT", [
            "3.1 Fees. Based on the Minimum Commitment, the estimated aggregate value of this Agreement over "
            "the two (2)-year Initial Term is nine hundred thousand dollars ($900,000); actual fees may vary "
            "with hours worked.",
            "3.2 Payment Terms. Client shall pay each undisputed invoice within thirty (30) days of the invoice "
            "date.",
            "3.3 Pricing Model. Services are billed on a time-and-materials basis.",
            "3.4 Price Escalation. Consultant's hourly rates may increase by up to three percent (3%) on each "
            "anniversary of the Effective Date.",
        ]),
        ("4. SERVICE LEVELS", [
            "4.1 Consultant shall acknowledge critical support requests within four (4) business hours and use "
            "best efforts to resolve them within two (2) business days.",
            "4.2 Consultant shall deliver a written analytics report to Client on a monthly basis.",
        ]),
        ("5. DATA RESIDENCY AND SECURITY", [
            "5.1 Data Residency. All Client data provided to Consultant shall be processed and stored "
            "exclusively within data centers located in the United States.",
        ]),
        ("6. LIMITATION OF LIABILITY", [
            "6.1 Except for liabilities arising from a Party's breach of confidentiality or indemnification "
            "obligations, each Party's total aggregate liability arising out of this Agreement shall not exceed "
            "one million dollars ($1,000,000).",
        ]),
        ("7. INDEMNIFICATION", [
            "7.1 Consultant shall defend, indemnify, and hold harmless Client from third-party claims arising "
            "out of Consultant's breach of this Agreement or infringement of a third party's intellectual "
            "property rights by the deliverables.",
        ]),
        ("8. INSURANCE", [
            "8.1 Throughout the Term, Consultant shall maintain Professional Liability insurance of not less "
            "than $2,000,000 per claim and Cyber Liability insurance of not less than $2,000,000 per occurrence.",
        ]),
        ("9. TERMINATION", [
            "9.1 Termination for Cause. Either Party may terminate this Agreement immediately upon written "
            "notice if the other Party commits a material breach and fails to cure it within thirty (30) days "
            "of notice.",
            "9.2 Termination for Convenience. Either Party may terminate this Agreement for convenience by "
            "giving the other Party not less than sixty (60) days' prior written notice.",
        ]),
        ("10. CHANGE OF CONTROL; ASSIGNMENT", [
            "10.1 Neither Party may assign this Agreement without the other Party's prior written consent, "
            "except in connection with a merger, acquisition, or sale of substantially all of its assets.",
        ]),
        ("11. GOVERNING LAW", [
            "11.1 This Agreement is governed by, and shall be construed in accordance with, the laws of the "
            "State of California, without regard to its conflict-of-laws principles. The state and federal "
            "courts located in San Francisco County, California shall have exclusive jurisdiction over any "
            "dispute arising out of this Agreement.",
        ]),
        ("12. GENERAL PROVISIONS", [
            "12.1 Entire Agreement. This Agreement, together with its Schedules, constitutes the entire "
            "agreement between the Parties with respect to its subject matter.",
        ]),
    ],
    sig=dict(
        vendor_name="Cascade Analytics Partners LLC", vendor_signee="Dana Whitfield", vendor_title="Managing Partner",
        client_name="Harrow & Vance LLP", client_signee="Gerald Vance", client_title="Chief Operating Officer",
        date_str="December 1, 2024",
    ),
)

# ---------------------------------------------------------------------------
# 5. SERVICE - Beacon Security Consulting Ltd / Whitfield & Cole Insurance plc
# ---------------------------------------------------------------------------
build(
    filename="service__beacon-security-consulting__penetration-testing-services-agreement.pdf",
    title="PENETRATION TESTING AND SECURITY CONSULTING SERVICES AGREEMENT",
    vendor_block="Beacon Security Consulting Ltd (&ldquo;Consultant&rdquo;)",
    client_block="Whitfield &amp; Cole Insurance plc (&ldquo;Client&rdquo;)",
    intro=[
        "This Penetration Testing and Security Consulting Services Agreement (this &ldquo;Agreement&rdquo;) is "
        "entered into and effective as of July 1, 2026 (the &ldquo;Effective Date&rdquo;) by and between Beacon "
        "Security Consulting Ltd, a company registered in England and Wales with its registered office at 31 "
        "Cheapside, London, EC2V 6DN, United Kingdom (&ldquo;Consultant&rdquo;), and Whitfield &amp; Cole "
        "Insurance plc, a company registered in England and Wales with its registered office at 4 Lombard Court, "
        "London, EC3V 9AA, United Kingdom (&ldquo;Client&rdquo;), each a &ldquo;Party&rdquo; and together the "
        "&ldquo;Parties.&rdquo;",
        "RECITALS. Consultant provides penetration testing and security consulting services, and Client wishes "
        "to engage Consultant to test and advise on its information systems on the terms below.",
    ],
    sections=[
        ("1. TERM AND RENEWAL", [
            "1.1 Initial Term. This Agreement commences on the Effective Date and continues for an initial term "
            "of three (3) years, expiring on June 30, 2029 (the &ldquo;Initial Term&rdquo;), unless terminated "
            "earlier under Section 9.",
            "1.2 Automatic Renewal. Upon expiry of the Initial Term, this Agreement automatically renews for "
            "successive one (1)-year periods, unless either Party gives the other written notice of non-renewal "
            "at least ninety (90) days before the end of the then-current term.",
        ]),
        ("2. SERVICES; EXCLUSIVITY; MINIMUM COMMITMENT", [
            "2.1 Consultant shall provide penetration testing, vulnerability assessment, and security advisory "
            "services as described in Schedule A.",
            "2.2 Exclusivity. During the Term, Consultant shall be Client's exclusive provider of penetration "
            "testing services for Client's production information systems.",
            "2.3 Minimum Commitment. The annual retainer fee includes a minimum of twelve (12) penetration-"
            "testing engagements per year.",
        ]),
        ("3. FEES AND PAYMENT", [
            "3.1 Fees. Client shall pay Consultant an annual retainer fee of two hundred twenty-five thousand "
            "pounds sterling (&pound;225,000), invoiced quarterly in advance. The aggregate value of this "
            "Agreement over the three (3)-year Initial Term is six hundred seventy-five thousand pounds sterling "
            "(&pound;675,000).",
            "3.2 Payment Terms. Client shall pay each undisputed invoice within thirty (30) days of the invoice "
            "date.",
            "3.3 Pricing Model. The Services are provided for a fixed annual retainer fee.",
            "3.4 Price Escalation. At the start of each Renewal Term, the annual retainer fee shall increase in "
            "line with UK CPI, capped at four percent (4%) per year.",
        ]),
        ("4. SERVICE LEVELS", [
            "4.1 Consultant shall report any critical vulnerability finding to Client within twenty-four (24) "
            "hours of discovery.",
            "4.2 Consultant shall deliver a final written report for each engagement within ten (10) business "
            "days of completion.",
        ]),
        ("5. DATA RESIDENCY AND CONFIDENTIALITY", [
            "5.1 Data Residency. All Client data, including test findings and vulnerability reports, shall be "
            "stored and processed exclusively within the United Kingdom.",
        ]),
        ("6. LIMITATION OF LIABILITY", [
            "6.1 Except for liability arising from a Party's breach of confidentiality or data protection "
            "obligations, which shall be unlimited, each Party's total aggregate liability arising out of this "
            "Agreement shall not exceed two million pounds sterling (&pound;2,000,000).",
        ]),
        ("7. INDEMNIFICATION", [
            "7.1 Consultant shall defend, indemnify, and hold harmless Client from third-party claims arising "
            "out of Consultant's breach of confidentiality or its gross negligence or wilful misconduct in "
            "performing the Services.",
        ]),
        ("8. INSURANCE", [
            "8.1 Throughout the Term, Consultant shall maintain Professional Indemnity insurance of not less "
            "than &pound;5,000,000 per claim and Cyber Liability insurance of not less than &pound;5,000,000 "
            "per occurrence.",
        ]),
        ("9. TERMINATION", [
            "9.1 Termination for Cause. Either Party may terminate this Agreement immediately upon written "
            "notice if the other Party commits a material breach and fails to cure it within thirty (30) days "
            "of notice.",
            "9.2 Termination for Convenience. Either Party may terminate this Agreement for convenience by "
            "giving the other Party not less than one hundred twenty (120) days' prior written notice.",
        ]),
        ("10. CHANGE OF CONTROL; ASSIGNMENT", [
            "10.1 Neither Party may assign this Agreement without the other Party's prior written consent, "
            "except in connection with a merger, acquisition, or sale of substantially all of its assets.",
        ]),
        ("11. GOVERNING LAW", [
            "11.1 This Agreement is governed by, and shall be construed in accordance with, the laws of England "
            "and Wales. The courts of England and Wales shall have exclusive jurisdiction over any dispute "
            "arising out of this Agreement.",
        ]),
        ("12. GENERAL PROVISIONS", [
            "12.1 Entire Agreement. This Agreement, together with its Schedules, constitutes the entire "
            "agreement between the Parties with respect to its subject matter.",
        ]),
    ],
    sig=dict(
        vendor_name="Beacon Security Consulting Ltd", vendor_signee="Fiona Argyle", vendor_title="Managing Director",
        client_name="Whitfield & Cole Insurance plc", client_signee="Hugo Whitfield", client_title="Chief Information Security Officer",
        date_str="July 1, 2026",
    ),
)

# ---------------------------------------------------------------------------
# 6. MAINTENANCE - Ferro Industrial Maintenance Services LLC / Bramwell Steelworks Inc.
# ---------------------------------------------------------------------------
build(
    filename="maintenance__ferro-industrial-maintenance__equipment-maintenance-agreement.pdf",
    title="INDUSTRIAL EQUIPMENT MAINTENANCE AGREEMENT",
    vendor_block="Ferro Industrial Maintenance Services LLC (&ldquo;Vendor&rdquo;)",
    client_block="Bramwell Steelworks Inc. (&ldquo;Customer&rdquo;)",
    intro=[
        "This Industrial Equipment Maintenance Agreement (this &ldquo;Agreement&rdquo;) is entered into and "
        "effective as of November 5, 2023 (the &ldquo;Effective Date&rdquo;) by and between Ferro Industrial "
        "Maintenance Services LLC, an Ohio limited liability company with its principal place of business at "
        "1200 Foundry Road, Cleveland, Ohio 44113 (&ldquo;Vendor&rdquo;), and Bramwell Steelworks Inc., an Ohio "
        "corporation with its principal place of business at 40 Mill Street, Youngstown, Ohio 44501 "
        "(&ldquo;Customer&rdquo;), each a &ldquo;Party&rdquo; and together the &ldquo;Parties.&rdquo;",
        "RECITALS. Vendor provides preventive and emergency maintenance services for industrial manufacturing "
        "equipment, and Customer wishes to engage Vendor to maintain the equipment at its Youngstown facility "
        "on the terms below.",
    ],
    sections=[
        ("1. TERM", [
            "1.1 Initial Term. This Agreement commences on the Effective Date and continues for a fixed term of "
            "three (3) years, expiring on November 5, 2026 (the &ldquo;Term&rdquo;), unless terminated earlier "
            "under Section 8. This Agreement does not renew automatically; a new agreement must be signed for "
            "maintenance services to continue beyond the Term.",
        ]),
        ("2. SERVICES; MINIMUM COMMITMENT", [
            "2.1 Vendor shall provide preventive maintenance, inspection, and emergency repair services for the "
            "equipment listed in Schedule A.",
            "2.2 Minimum Commitment. Vendor shall perform a minimum of twenty-four (24) scheduled preventive-"
            "maintenance visits per year.",
        ]),
        ("3. FEES AND PAYMENT", [
            "3.1 Fees. Customer shall pay Vendor a fixed annual maintenance fee of one hundred eighty thousand "
            "dollars ($180,000), invoiced quarterly in advance. The aggregate value of this Agreement over the "
            "three (3)-year Term is five hundred forty thousand dollars ($540,000).",
            "3.2 Payment Terms. Customer shall pay each undisputed invoice within thirty (30) days of the "
            "invoice date.",
            "3.3 Pricing Model. Services are provided for a fixed annual fee; the fee does not increase during "
            "the Term.",
        ]),
        ("4. SERVICE LEVELS", [
            "4.1 Vendor shall respond to an emergency callout within four (4) hours of notification.",
            "4.2 Vendor shall use commercially reasonable efforts to maintain equipment uptime of at least "
            "ninety-eight percent (98%). If Vendor fails to meet the four-hour response target more than twice "
            "in a calendar quarter, Customer shall be entitled to a service credit of 5% of that quarter's fees.",
        ]),
        ("5. LIMITATION OF LIABILITY", [
            "5.1 Except for liabilities arising from a Party's breach of confidentiality or indemnification "
            "obligations, each Party's total aggregate liability arising out of this Agreement shall not exceed "
            "seven hundred fifty thousand dollars ($750,000).",
        ]),
        ("6. INDEMNIFICATION", [
            "6.1 Vendor shall defend, indemnify, and hold harmless Customer from third-party claims for property "
            "damage or bodily injury arising out of Vendor's negligence in performing the Services.",
        ]),
        ("7. INSURANCE", [
            "7.1 Throughout the Term, Vendor shall maintain Commercial General Liability insurance of not less "
            "than $2,000,000 per occurrence and statutory Workers' Compensation and Employer's Liability "
            "insurance as required under Ohio law.",
        ]),
        ("8. TERMINATION", [
            "8.1 Termination for Cause. Either Party may terminate this Agreement immediately upon written "
            "notice if the other Party commits a material breach and fails to cure it within thirty (30) days "
            "of notice. There is no right to terminate this Agreement for convenience prior to expiry of the Term.",
        ]),
        ("9. CHANGE OF CONTROL; ASSIGNMENT", [
            "9.1 Neither Party may assign this Agreement without the other Party's prior written consent, "
            "except in connection with a merger, acquisition, or sale of substantially all of its assets.",
        ]),
        ("10. GOVERNING LAW", [
            "10.1 This Agreement is governed by, and shall be construed in accordance with, the laws of the "
            "State of Ohio, without regard to its conflict-of-laws principles. The state and federal courts "
            "located in Cuyahoga County, Ohio shall have exclusive jurisdiction over any dispute arising out of "
            "this Agreement.",
        ]),
        ("11. GENERAL PROVISIONS", [
            "11.1 Entire Agreement. This Agreement, together with its Schedules, constitutes the entire "
            "agreement between the Parties with respect to its subject matter.",
        ]),
    ],
    sig=dict(
        vendor_name="Ferro Industrial Maintenance Services LLC", vendor_signee="Carlos Medina", vendor_title="General Manager",
        client_name="Bramwell Steelworks Inc.", client_signee="Susan Bramwell", client_title="Plant Director",
        date_str="November 5, 2023",
    ),
)

# ---------------------------------------------------------------------------
# 7. MAINTENANCE - Pinnacle IT Support Group Ltd / Thornfield Legal Services LLP
# ---------------------------------------------------------------------------
build(
    filename="maintenance__pinnacle-it-support-group__it-support-and-maintenance-agreement.pdf",
    title="IT SUPPORT AND MAINTENANCE AGREEMENT",
    vendor_block="Pinnacle IT Support Group Ltd (&ldquo;Vendor&rdquo;)",
    client_block="Thornfield Legal Services LLP (&ldquo;Customer&rdquo;)",
    intro=[
        "This IT Support and Maintenance Agreement (this &ldquo;Agreement&rdquo;) is entered into and effective "
        "as of May 1, 2025 (the &ldquo;Effective Date&rdquo;) by and between Pinnacle IT Support Group Ltd, a "
        "company registered in England and Wales with its registered office at 18 Wharf Road, Leeds, LS1 4DY, "
        "United Kingdom (&ldquo;Vendor&rdquo;), and Thornfield Legal Services LLP, a limited liability "
        "partnership with its registered office at 9 Chancery Row, Leeds, LS2 7JB, United Kingdom "
        "(&ldquo;Customer&rdquo;), each a &ldquo;Party&rdquo; and together the &ldquo;Parties.&rdquo;",
        "RECITALS. Vendor provides managed IT support and infrastructure maintenance services, and Customer "
        "wishes to engage Vendor to support its office IT environment on the terms below.",
    ],
    sections=[
        ("1. TERM AND RENEWAL", [
            "1.1 Initial Term. This Agreement commences on the Effective Date and continues for an initial term "
            "of two (2) years, expiring on April 30, 2027 (the &ldquo;Initial Term&rdquo;), unless terminated "
            "earlier under Section 9.",
            "1.2 Automatic Renewal. Upon expiry of the Initial Term, this Agreement automatically renews for "
            "successive one (1)-year periods, unless either Party gives the other written notice of non-renewal "
            "at least thirty (30) days before the end of the then-current term.",
        ]),
        ("2. SERVICES; MINIMUM COMMITMENT", [
            "2.1 Vendor shall provide helpdesk support, infrastructure monitoring, and patch management services "
            "for Customer's IT estate as described in Schedule A.",
            "2.2 Minimum Commitment. The subscription fee covers a minimum of one hundred fifty (150) supported "
            "devices; Customer shall pay a per-device supplement for devices in excess of this minimum.",
        ]),
        ("3. FEES AND PAYMENT", [
            "3.1 Fees. Customer shall pay Vendor an annual subscription fee of one hundred eight thousand pounds "
            "sterling (&pound;108,000), invoiced monthly in advance. The aggregate value of this Agreement over "
            "the two (2)-year Initial Term is two hundred sixteen thousand pounds sterling (&pound;216,000).",
            "3.2 Payment Terms. Customer shall pay each undisputed invoice within fifteen (15) days of the "
            "invoice date.",
            "3.3 Pricing Model. The Services are provided on a per-device monthly subscription basis.",
            "3.4 Price Escalation. The annual subscription fee shall increase by a fixed three percent (3%) on "
            "each anniversary of the Effective Date.",
        ]),
        ("4. SERVICE LEVELS", [
            "4.1 Vendor shall acknowledge Priority-1 support tickets within one (1) hour and use best efforts "
            "to resolve them within four (4) hours.",
            "4.2 Vendor shall maintain uptime of Customer's managed infrastructure of at least 99.5% per month, "
            "measured as described in Schedule B. If monthly uptime falls below 99.5%, Customer shall receive a "
            "service credit of 5% of that month's fees for each full percentage point of shortfall, up to a "
            "maximum of 20% of that month's fees.",
        ]),
        ("5. DATA RESIDENCY AND CONFIDENTIALITY", [
            "5.1 Data Residency. Given Customer's obligations of client confidentiality as a law firm, all "
            "Customer data and backups shall be stored and processed exclusively within the United Kingdom.",
        ]),
        ("6. LIMITATION OF LIABILITY", [
            "6.1 Except for liabilities arising from a Party's breach of confidentiality or indemnification "
            "obligations, each Party's total aggregate liability arising out of this Agreement shall not exceed "
            "four hundred thousand pounds sterling (&pound;400,000).",
        ]),
        ("7. INDEMNIFICATION", [
            "7.1 Vendor shall defend, indemnify, and hold harmless Customer from third-party claims arising out "
            "of Vendor's breach of confidentiality or its gross negligence in performing the Services.",
        ]),
        ("8. INSURANCE", [
            "8.1 Throughout the Term, Vendor shall maintain Professional Indemnity insurance of not less than "
            "&pound;1,000,000 per claim and Cyber Liability insurance of not less than &pound;1,000,000 per "
            "occurrence.",
        ]),
        ("9. TERMINATION", [
            "9.1 Termination for Cause. Either Party may terminate this Agreement immediately upon written "
            "notice if the other Party commits a material breach and fails to cure it within thirty (30) days "
            "of notice.",
            "9.2 Termination for Convenience. Either Party may terminate this Agreement for convenience by "
            "giving the other Party not less than sixty (60) days' prior written notice.",
        ]),
        ("10. CHANGE OF CONTROL; ASSIGNMENT", [
            "10.1 Neither Party may assign this Agreement without the other Party's prior written consent, "
            "except in connection with a merger, acquisition, or sale of substantially all of its assets.",
        ]),
        ("11. GOVERNING LAW", [
            "11.1 This Agreement is governed by, and shall be construed in accordance with, the laws of England "
            "and Wales. The courts of England and Wales shall have exclusive jurisdiction over any dispute "
            "arising out of this Agreement.",
        ]),
        ("12. GENERAL PROVISIONS", [
            "12.1 Entire Agreement. This Agreement, together with its Schedules, constitutes the entire "
            "agreement between the Parties with respect to its subject matter.",
        ]),
    ],
    sig=dict(
        vendor_name="Pinnacle IT Support Group Ltd", vendor_signee="Nadia Farouk", vendor_title="Head of Client Services",
        client_name="Thornfield Legal Services LLP", client_signee="Edmund Thornfield", client_title="Managing Partner",
        date_str="May 1, 2025",
    ),
)

# ---------------------------------------------------------------------------
# 8. OUTSOURCING - Meritus BPO Solutions Pvt Ltd / Coastal Home Insurance Co.
# ---------------------------------------------------------------------------
build(
    filename="outsourcing__meritus-bpo-solutions__claims-processing-outsourcing-agreement.pdf",
    title="CLAIMS PROCESSING OUTSOURCING AGREEMENT",
    vendor_block="Meritus BPO Solutions Pvt Ltd (&ldquo;Provider&rdquo;)",
    client_block="Coastal Home Insurance Co. (&ldquo;Client&rdquo;)",
    intro=[
        "This Claims Processing Outsourcing Agreement (this &ldquo;Agreement&rdquo;) is entered into and "
        "effective as of December 20, 2024 (the &ldquo;Effective Date&rdquo;) by and between Meritus BPO "
        "Solutions Pvt Ltd, a company incorporated in India with its principal place of business at Prestige "
        "Tech Park, Bengaluru, Karnataka 560103, India (&ldquo;Provider&rdquo;), and Coastal Home Insurance Co., "
        "a Delaware corporation with its principal place of business at 500 Harbor Boulevard, Wilmington, "
        "Delaware 19801 (&ldquo;Client&rdquo;), each a &ldquo;Party&rdquo; and together the &ldquo;Parties.&rdquo;",
        "RECITALS. Provider operates outsourced claims-processing and customer-support centers, and Client "
        "wishes to outsource its first-notice-of-loss claims processing and policyholder support functions to "
        "Provider on the terms below.",
    ],
    sections=[
        ("1. TERM AND RENEWAL", [
            "1.1 Initial Term. This Agreement commences on the Effective Date and continues for an initial term "
            "of two (2) years, expiring on December 20, 2026 (the &ldquo;Initial Term&rdquo;), unless terminated "
            "earlier under Section 9.",
            "1.2 Automatic Renewal. Upon expiry of the Initial Term, this Agreement automatically renews for "
            "successive one (1)-year periods, unless either Party gives the other written notice of non-renewal "
            "at least ninety (90) days before the end of the then-current term.",
        ]),
        ("2. SERVICES; EXCLUSIVITY; MINIMUM COMMITMENT", [
            "2.1 Provider shall perform the outsourced claims-processing and policyholder support functions "
            "described in Schedule A (the &ldquo;Services&rdquo;).",
            "2.2 Exclusivity. During the Term, Provider shall be Client's exclusive provider of the outsourced "
            "claims-processing functions described in Schedule A.",
            "2.3 Minimum Commitment. Client commits to a minimum monthly billable volume of forty thousand "
            "(40,000) transactions; if actual monthly volume is lower, Client shall pay Provider a minimum fee "
            "calculated on 40,000 transactions.",
        ]),
        ("3. FEES AND PAYMENT", [
            "3.1 Fees. Based on the Minimum Commitment, the aggregate value of this Agreement over the two "
            "(2)-year Initial Term is estimated at three million six hundred thousand dollars ($3,600,000).",
            "3.2 Payment Terms. Client shall pay each undisputed invoice within thirty (30) days of the invoice "
            "date.",
            "3.3 Pricing Model. Fees are billed on a usage basis, per transaction processed and per FTE-hour of "
            "support delivered, as set out in Schedule A.",
            "3.4 Price Escalation. At each renewal, per-transaction and per-FTE-hour rates may increase in line "
            "with the Consumer Price Index for India, capped at six percent (6%) per year.",
        ]),
        ("4. SERVICE LEVELS", [
            "4.1 Provider shall maintain an average handle time within Client's target thresholds and a "
            "first-call resolution rate of at least eighty-five percent (85%), each measured monthly per "
            "Schedule B.",
            "4.2 If Provider fails to meet the service levels in Schedule B in a given month, Client shall be "
            "entitled to a service credit of up to fifteen percent (15%) of that month's fees.",
        ]),
        ("5. DATA RESIDENCY AND SECURITY", [
            "5.1 Data Residency. Client policyholder personal data shall be processed only within SOC 2-"
            "certified facilities located in India and the United States. Provider shall not transfer such data "
            "to any other jurisdiction without Client's prior written consent.",
        ]),
        ("6. LIMITATION OF LIABILITY", [
            "6.1 Except for liability arising from a Party's breach of confidentiality or data protection "
            "obligations, which shall be unlimited, each Party's total aggregate liability arising out of this "
            "Agreement shall not exceed four million dollars ($4,000,000).",
        ]),
        ("7. INDEMNIFICATION", [
            "7.1 Provider shall defend, indemnify, and hold harmless Client from third-party claims arising out "
            "of (a) a data breach involving policyholder personal data, (b) Provider's negligence in performing "
            "the Services, or (c) infringement of a third party's intellectual property rights.",
        ]),
        ("8. INSURANCE", [
            "8.1 Throughout the Term, Provider shall maintain Professional Liability insurance of not less than "
            "$5,000,000 per claim and Cyber Liability insurance of not less than $10,000,000 per occurrence.",
        ]),
        ("9. TERMINATION", [
            "9.1 Termination for Cause. Either Party may terminate this Agreement immediately upon written "
            "notice if the other Party commits a material breach and fails to cure it within thirty (30) days "
            "of notice.",
            "9.2 Termination for Convenience. Either Party may terminate this Agreement for convenience by "
            "giving the other Party not less than one hundred twenty (120) days' prior written notice.",
        ]),
        ("10. CHANGE OF CONTROL; ASSIGNMENT", [
            "10.1 Neither Party may assign this Agreement without the other Party's prior written consent, "
            "except in connection with a merger, acquisition, or sale of substantially all of its assets.",
            "10.2 If Provider undergoes a Change of Control involving a direct competitor of Client, Client may "
            "terminate this Agreement on thirty (30) days' written notice given within ninety (90) days of "
            "becoming aware of the Change of Control.",
        ]),
        ("11. GOVERNING LAW", [
            "11.1 This Agreement is governed by, and shall be construed in accordance with, the laws of the "
            "State of New York, without regard to its conflict-of-laws principles. The state and federal courts "
            "located in New York County, New York shall have exclusive jurisdiction over any dispute arising "
            "out of this Agreement.",
        ]),
        ("12. GENERAL PROVISIONS", [
            "12.1 Entire Agreement. This Agreement, together with its Schedules, constitutes the entire "
            "agreement between the Parties with respect to its subject matter.",
        ]),
    ],
    sig=dict(
        vendor_name="Meritus BPO Solutions Pvt Ltd", vendor_signee="Anjali Rao", vendor_title="Chief Delivery Officer",
        client_name="Coastal Home Insurance Co.", client_signee="Walter Kominsky", client_title="VP, Claims Operations",
        date_str="December 20, 2024",
    ),
)

# ---------------------------------------------------------------------------
# 9. OUTSOURCING - Vertex Manufacturing Outsource Partners Ltd / Solent Audio Equipment Ltd
# ---------------------------------------------------------------------------
build(
    filename="outsourcing__vertex-manufacturing-outsource-partners__assembly-outsourcing-agreement.pdf",
    title="ASSEMBLY MANUFACTURING OUTSOURCING AGREEMENT",
    vendor_block="Vertex Manufacturing Outsource Partners Ltd (&ldquo;Provider&rdquo;)",
    client_block="Solent Audio Equipment Ltd (&ldquo;Client&rdquo;)",
    intro=[
        "This Assembly Manufacturing Outsourcing Agreement (this &ldquo;Agreement&rdquo;) is entered into and "
        "effective as of January 10, 2026 (the &ldquo;Effective Date&rdquo;) by and between Vertex Manufacturing "
        "Outsource Partners Ltd, a company registered in England and Wales with its registered office at 12 "
        "Dockside Way, Southampton, SO14 3XB, United Kingdom, operating an assembly facility in Haiphong, "
        "Vietnam (&ldquo;Provider&rdquo;), and Solent Audio Equipment Ltd, a company registered in England and "
        "Wales with its registered office at 5 Harbourside Road, Southampton, SO15 2AA, United Kingdom "
        "(&ldquo;Client&rdquo;), each a &ldquo;Party&rdquo; and together the &ldquo;Parties.&rdquo;",
        "RECITALS. Provider operates contract assembly manufacturing facilities, and Client wishes to outsource "
        "the assembly of its audio equipment products to Provider on the terms below.",
    ],
    sections=[
        ("1. TERM AND RENEWAL", [
            "1.1 Initial Term. This Agreement commences on the Effective Date and continues for an initial term "
            "of four (4) years, expiring on January 9, 2030 (the &ldquo;Initial Term&rdquo;), unless terminated "
            "earlier under Section 9.",
            "1.2 Automatic Renewal. Upon expiry of the Initial Term, this Agreement automatically renews for "
            "successive two (2)-year periods, unless either Party gives the other written notice of non-renewal "
            "at least sixty (60) days before the end of the then-current term.",
        ]),
        ("2. SERVICES; MINIMUM COMMITMENT", [
            "2.1 Provider shall assemble Client's audio equipment products in accordance with the specifications "
            "in Schedule A.",
            "2.2 Minimum Commitment. Client commits to a minimum annual order volume of one hundred thousand "
            "(100,000) assembled units for each year of the Term.",
        ]),
        ("3. FEES AND PAYMENT", [
            "3.1 Fees. Based on the Minimum Commitment, the aggregate value of this Agreement over the four "
            "(4)-year Initial Term is estimated at eight million pounds sterling (&pound;8,000,000).",
            "3.2 Payment Terms. Client shall pay each undisputed invoice within forty-five (45) days of the "
            "invoice date.",
            "3.3 Pricing Model. Units are assembled at fixed per-unit fees set out in Schedule A.",
            "3.4 Price Escalation. Provider may increase per-unit fees once per calendar year by the lesser of "
            "(i) five percent (5%), or (ii) the percentage increase in a named raw-materials index specified in "
            "Schedule A.",
        ]),
        ("4. QUALITY AND DELIVERY PERFORMANCE", [
            "4.1 Provider shall use commercially reasonable efforts to achieve an on-time shipment rate of at "
            "least ninety-six percent (96%) and a defect rate below zero point five percent (0.5%), each "
            "measured quarterly.",
            "4.2 If Provider's on-time shipment rate falls below the target in a given quarter, Client shall be "
            "entitled to a service credit against the affected shipment's value, up to a maximum of ten percent "
            "(10%) of that shipment's value.",
        ]),
        ("5. LIMITATION OF LIABILITY", [
            "5.1 Except for liabilities arising from a Party's breach of confidentiality, IP infringement, or "
            "indemnification obligations, each Party's total aggregate liability arising out of this Agreement "
            "shall not exceed three million pounds sterling (&pound;3,000,000).",
        ]),
        ("6. INDEMNIFICATION", [
            "6.1 Provider shall defend, indemnify, and hold harmless Client from third-party claims arising out "
            "of (a) defective assembled products, or (b) infringement of a third party's intellectual property "
            "rights arising from Provider's assembly processes.",
        ]),
        ("7. INSURANCE", [
            "7.1 Throughout the Term, Provider shall maintain Product Liability insurance of not less than "
            "&pound;5,000,000 per occurrence and Commercial General Liability insurance of not less than "
            "&pound;2,000,000 per occurrence.",
        ]),
        ("8. TERMINATION", [
            "8.1 Termination for Cause. Either Party may terminate this Agreement immediately upon written "
            "notice if the other Party commits a material breach and fails to cure it within thirty (30) days "
            "of notice.",
            "8.2 Termination for Convenience. Either Party may terminate this Agreement for convenience by "
            "giving the other Party not less than one hundred eighty (180) days' prior written notice.",
        ]),
        ("9. CHANGE OF CONTROL; ASSIGNMENT", [
            "9.1 Neither Party may assign this Agreement without the other Party's prior written consent, "
            "except in connection with a merger, acquisition, or sale of substantially all of its assets.",
            "9.2 If Provider undergoes a Change of Control involving a direct competitor of Client, Client may "
            "terminate this Agreement on thirty (30) days' written notice given within ninety (90) days of "
            "becoming aware of the Change of Control.",
        ]),
        ("10. GOVERNING LAW", [
            "10.1 This Agreement is governed by, and shall be construed in accordance with, the laws of England "
            "and Wales. The courts of England and Wales shall have exclusive jurisdiction over any dispute "
            "arising out of this Agreement.",
        ]),
        ("11. GENERAL PROVISIONS", [
            "11.1 Entire Agreement. This Agreement, together with its Schedules, constitutes the entire "
            "agreement between the Parties with respect to its subject matter.",
        ]),
    ],
    sig=dict(
        vendor_name="Vertex Manufacturing Outsource Partners Ltd", vendor_signee="Minh Tran", vendor_title="Chief Operating Officer",
        client_name="Solent Audio Equipment Ltd", client_signee="Rosalind Hale", client_title="Head of Operations",
        date_str="January 10, 2026",
    ),
)

print("\nDone. Note: hosting__northbridge-data-systems__cloud-hosting-agreement.pdf is kept as-is (not regenerated).")
