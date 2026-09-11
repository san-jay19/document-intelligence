import json
import os
import re

from dotenv import load_dotenv
from groq import Groq

from backend.app.schemas.extraction import ExtractionResult


# =========================================================
# Environment
# =========================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError(
        "GROQ_API_KEY is not configured."
    )


# =========================================================
# Groq Client
# =========================================================

client = Groq(
    api_key=api_key
)


# =========================================================
# Confidence
# =========================================================

def calculate_average_confidence(
    extraction: ExtractionResult,
) -> float | None:
    """
    Calculate average confidence across extracted fields.
    """

    values = []

    for field in extraction.fields:

        if field.confidence is None:
            continue

        try:
            confidence = float(
                field.confidence
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        confidence = max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )

        values.append(
            confidence
        )

    if not values:
        return None

    return round(
        sum(values) / len(values),
        2,
    )


# =========================================================
# Clean Model Response
# =========================================================

def _clean_response(
    content: str,
) -> str:
    """
    Remove common markdown/code-fence formatting.
    """

    if not content:
        raise ValueError(
            "Groq returned an empty response."
        )

    content = content.strip()

    content = re.sub(
        r"^\s*```json\s*",
        "",
        content,
        flags=re.IGNORECASE,
    )

    content = re.sub(
        r"^\s*```\s*",
        "",
        content,
    )

    content = re.sub(
        r"\s*```\s*$",
        "",
        content,
    )

    return content.strip()


# =========================================================
# JSON Parsing
# =========================================================

def _parse_json_response(
    content: str,
) -> dict:
    """
    Parse the AI response as JSON.

    First tries the complete response.
    Then attempts to extract an embedded JSON object.
    """

    content = _clean_response(
        content
    )

    # -----------------------------------------------
    # Complete response
    # -----------------------------------------------

    try:

        data = json.loads(
            content
        )

        if isinstance(data, dict):
            return data

    except json.JSONDecodeError:
        pass

    # -----------------------------------------------
    # Embedded JSON object
    # -----------------------------------------------

    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "Groq response does not contain a JSON object."
        )

    json_text = content[
        start:end + 1
    ]

    try:

        data = json.loads(
            json_text
        )

    except json.JSONDecodeError as exc:

        raise ValueError(
            "Groq returned invalid JSON.\n\n"
            f"Model response:\n{content}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            "Groq response must be a JSON object."
        )

    return data


# =========================================================
# Normalize Fields
# =========================================================

def _normalize_fields(
    fields,
) -> list[dict]:
    """
    Normalize extracted fields.
    """

    if fields is None:
        return []

    if not isinstance(
        fields,
        list,
    ):
        return []

    normalized = []

    for field in fields:

        if not isinstance(
            field,
            dict,
        ):
            continue

        name = field.get(
            "name"
        )

        if not name:
            continue

        confidence = field.get(
            "confidence"
        )

        if confidence is not None:

            try:
                confidence = float(
                    confidence
                )

            except (
                TypeError,
                ValueError,
            ):
                confidence = None

        if confidence is not None:

            confidence = max(
                0.0,
                min(
                    1.0,
                    confidence,
                ),
            )

        evidence = field.get(
            "evidence"
        )

        if evidence is not None:
            evidence = str(
                evidence
            )

        normalized.append(
            {
                "name": str(name),

                "value": field.get(
                    "value"
                ),

                "evidence": evidence,

                "confidence": confidence,
            }
        )

    return normalized


# =========================================================
# Normalize Tables
# =========================================================

def _normalize_tables(
    tables,
) -> list[dict]:
    """
    Normalize extracted tables.
    """

    if tables is None:
        return []

    if not isinstance(
        tables,
        list,
    ):
        return []

    normalized = []

    for table in tables:

        if not isinstance(
            table,
            dict,
        ):
            continue

        table_name = table.get(
            "table_name"
        )

        if not table_name:

            table_name = table.get(
                "name",
                "Table",
            )

        headers = table.get(
            "headers"
        )

        if headers is None:

            headers = table.get(
                "columns",
                [],
            )

        rows = table.get(
            "rows",
            [],
        )

        if not isinstance(
            headers,
            list,
        ):
            headers = []

        if not isinstance(
            rows,
            list,
        ):
            rows = []

        normalized_headers = [
            str(header)
            for header in headers
        ]

        normalized_rows = []

        for row in rows:

            if isinstance(
                row,
                list,
            ):

                normalized_rows.append(
                    row
                )

            elif isinstance(
                row,
                dict,
            ):

                normalized_row = []

                for header in normalized_headers:

                    normalized_row.append(
                        row.get(header)
                    )

                normalized_rows.append(
                    normalized_row
                )

        normalized.append(
            {
                "table_name": str(
                    table_name
                ),

                "headers": normalized_headers,

                "rows": normalized_rows,
            }
        )

    return normalized


# =========================================================
# Normalize Complete Response
# =========================================================

def _normalize_extraction(
    data: dict,
) -> dict:
    """
    Normalize the AI response to the application's format.
    """

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "AI response must be a JSON object."
        )

    document_type = data.get(
        "document_type",
        "unknown",
    )

    return {
        "document_type": str(
            document_type
        ),

        "fields": _normalize_fields(
            data.get(
                "fields",
                [],
            )
        ),

        "tables": _normalize_tables(
            data.get(
                "tables",
                [],
            )
        ),
    }


# =========================================================
# Main Extraction Function
# =========================================================

def extract_document_data(
    document_text: str,
    document_type: str,
) -> ExtractionResult:
    """
    Extract fields and tables from OCR text.

    Groq performs semantic extraction.
    The application performs normalization and validation.
    """

    if not document_text.strip():
        raise ValueError(
            "Document text cannot be empty."
        )

    document_type = (
        document_type
        .strip()
        .lower()
    )

    # =====================================================
    # System Prompt
    # =====================================================

    system_prompt = """
You are a financial document extraction engine.

Extract structured information from OCR text.

Return ONLY ONE valid JSON object.

Required top-level structure:

{
  "document_type": "...",
  "fields": [],
  "tables": []
}

Field object:

{
  "name": "...",
  "value": "...",
  "evidence": "...",
  "confidence": 0.0
}

Table object:

{
  "table_name": "...",
  "headers": ["..."],
  "rows": [
    ["..."]
  ]
}

Rules:

- Extract only information present in OCR.
- Never invent or guess values.
- Extract all meaningful visible fields.
- Extract all meaningful financial line items.
- Extract all meaningful tables.
- Preserve comparative periods.
- Preserve numbers exactly.
- Parentheses indicate negative values.
- Preserve currencies and units.
- Use null for missing/unreadable values.
- Do not calculate anything.
- Do not reconcile anything.
- Do not add explanations.
- Do not use markdown.
- Do not use code fences.
- Return JSON only.

For financial statements, comparative periods must be separate columns.

For Cash Flow Statements specifically, extract:
- operating activities
- every operating line item
- operating subtotal/total
- investing activities
- every investing line item
- investing subtotal/total
- financing activities
- every financing line item
- financing subtotal/total
- FX/exchange/translation adjustments
- net increase/decrease in cash
- opening cash
- closing cash
- all other visible rows
"""


    # =====================================================
    # User Prompt
    # =====================================================

    user_prompt = f"""
Document type:
{document_type}

Extract the following OCR document.

IMPORTANT:
Return ALL meaningful financial rows and comparative
period values present in the OCR.

Do not calculate values.

For Cash Flow Statements:
- keep all operating rows
- keep all investing rows
- keep all financing rows
- keep opening cash
- keep closing cash
- keep net increase/decrease
- keep FX/translation adjustments
- keep comparative years as separate columns
- preserve parentheses as negative values
- preserve every visible row

OCR:
-------------------------
{document_text}
-------------------------

Return ONLY JSON.
"""


    # =====================================================
    # Groq Request
    # =====================================================

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",

            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],

            temperature=0,

            # GPT-OSS 20B supports up to 65,536
            # completion tokens.
            max_completion_tokens=32768,

            # Reduce reasoning overhead so more of the
            # completion budget is available for extraction.
            reasoning_effort="low",

            # Prevent reasoning text from being returned
            # in message.content.
            include_reasoning=False,
        )

    except Exception as exc:

        raise RuntimeError(
            f"Groq API request failed: {exc}"
        ) from exc


    # =====================================================
    # Read Model Response
    # =====================================================

    if not response.choices:

        raise RuntimeError(
            "Groq returned no choices."
        )

    choice = response.choices[0]
    message = choice.message

    content = message.content

    if not content:

        raise RuntimeError(
            "Groq returned no final content. "
            f"finish_reason={choice.finish_reason}; "
            f"reasoning={getattr(message, 'reasoning', None)}"
        )


    # =====================================================
    # Parse
    # =====================================================

    try:

        data = _parse_json_response(
            content
        )

    except Exception as exc:

        raise RuntimeError(
            f"Could not parse Groq response: {exc}"
        ) from exc


    # =====================================================
    # Normalize
    # =====================================================

    normalized = _normalize_extraction(
        data
    )


    # =====================================================
    # Validate
    # =====================================================

    try:

        return ExtractionResult.model_validate(
            normalized
        )

    except Exception as exc:

        raise RuntimeError(
            "AI response could not be converted "
            f"to the application model: {exc}"
        ) from exc