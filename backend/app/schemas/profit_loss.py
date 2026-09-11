from pydantic import BaseModel, ConfigDict


class ProfitLossItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str
    current_year: float | None
    previous_year: float | None


class ProfitLossData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: str
    reporting_date: str | None

    items: list[ProfitLossItem]

    profit_before_tax: float | None
    income_tax: float | None
    profit_after_tax: float | None