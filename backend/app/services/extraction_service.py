from typing import Optional

from openai import OpenAI
from pydantic import BaseModel

from backend.app.core.config import settings


# =========================================================
# STRUCTURED OUTPUT MODELS
# =========================================================

class ExtractedField(BaseModel):
    name: str
    value: Optional[str]
    page_number: Optional[int]
    evidence: Optional[str]


class PeriodValue(BaseModel):
    period: str
    value: Optional[str]


class LineItem(BaseModel):
    description: str
    values: list[PeriodValue]
    page_number: Optional[int]
    evidence: Optional[str]


class ExtractedDocument(BaseModel):
    document_title: Optional[str]
    entity_name: Optional[str]
    currency: Optional[str]

    periods: list[str]

    fields: list[ExtractedField]

    line_items: list[LineItem]

    notes: list[str]


# =========================================================
# OPENAI CLIENT
# =========================================================

client = OpenAI(
    api_key=settings.openai_api_key
)


# =========================================================
# EXTRACTION INSTRUCTIONS
# =========================================================

SYSTEM_PROMPT = """
You are a financial document extraction engine.

Extract the complete information contained in the supplied document.

IMPORTANT RULES:

1. Extract ALL meaningful visible information.
2. Do NOT invent, guess, infer, or calculate values.
3. If a value is not present or unreadable, return null.
4. Preserve financial line-item descriptions as closely as possible.
5. Extract document title, entity/company name, currency and reporting periods.
6. Extract every visible financial field.
7. Extract every visible financial line item.
8. Extract comparative-period values separately when present.
9. Parentheses/brackets around numbers indicate negative values.
10. Preserve the source value accurately.
11. Evidence must be a short excerpt copied from the source text.

12. The source text contains explicit page markers such as:
--- PAGE 1 ---
--- PAGE 2 ---
--- PAGE 3 ---

Use ONLY these markers to determine page_number.

page_number MUST be an integer corresponding to the actual page:
1, 2, 3, etc.

Never use line numbers, years, amounts, character positions, or any
other number from the document as a page number.

If the page cannot be determined, return null.
13. Do NOT perform financial validation. Only extract source information.
14. Do not omit a visible field merely because it is not in a predefined list.
15. Financial tables must be treated as row-based tables.

16. The OCR text preserves approximate horizontal spacing between
financial columns. Use that spacing when determining which values
belong to which row.

17. Never move a number from one row to another.

18. Never use a number from a nearby row merely because the value
looks financially plausible.

19. For comparative statements, identify the reporting-period columns
from the document headers before assigning values.

20. Each line item must contain only values belonging to that exact
source row.

21. If a row's value-to-column relationship cannot be determined
reliably, return null rather than guessing.

22. Evidence should reproduce the complete source row whenever
possible, including the description and associated values.

23. Page numbers MUST correspond to the explicit PAGE markers.

DOCUMENT TYPES:

Invoice:
Extract invoice metadata, parties, dates, amounts, taxes, discounts,
payment information and every visible line item.

Balance Sheet:
Extract all visible assets, liabilities, capital/equity and related
financial line items for every visible reporting period.

Profit & Loss:
Extract all visible revenue, income, expense, profit, tax and related
financial line items for every visible reporting period.

Cash Flow Statement:
Extract all visible operating, investing, financing and cash-balance
line items for every visible reporting period.

For line_items:
- description = the source line-item name
- values = one value for each reporting period
- preserve the original value as text

For fields:
Use fields for important named values that are not naturally represented
as repeated financial line items.
"""


# =========================================================
# EXTRACTION FUNCTION
# =========================================================

def extract_document_data(
    document_text: str,
    document_type: str
) -> ExtractedDocument:

    user_prompt = f"""
Document type:
{document_type}

Extract the complete contents of the following document.

SOURCE DOCUMENT TEXT
====================
{document_text}
====================

Return only the structured extraction.
"""

    response = client.responses.parse(
        model=settings.openai_model,

        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],

        text_format=ExtractedDocument
    )

    if response.output_parsed is None:
        raise RuntimeError(
            "The AI model did not return structured extraction data."
        )

    return response.output_parsed