from typing import Any

from pydantic import BaseModel, Field


class ExtractedField(BaseModel):
    """
    A single AI-extracted field.
    """

    name: str
    value: Any = None
    evidence: str | None = None
    confidence: float | None = None


class ExtractedTable(BaseModel):
    """
    A table extracted by the AI.
    """

    table_name: str

    headers: list[str] = Field(
        default_factory=list
    )

    rows: list[list[Any]] = Field(
        default_factory=list
    )


class ExtractionResult(BaseModel):
    """
    Generic document extraction result.

    This deliberately does not contain invoice-specific
    or balance-sheet-specific fields because the AI needs
    to support different document layouts.
    """

    document_type: str

    fields: list[ExtractedField] = Field(
        default_factory=list
    )

    tables: list[ExtractedTable] = Field(
        default_factory=list
    )