from pydantic import BaseModel, ConfigDict


class InvoiceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str
    quantity: float | None
    net_price: float | None
    net_worth: float | None
    vat_percent: float | None
    gross_worth: float | None


class InvoiceData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: str
    invoice_number: str | None
    issue_date: str | None

    seller: str | None
    client: str | None

    items: list[InvoiceItem]

    vat_amount: float | None
    total_amount: float | None