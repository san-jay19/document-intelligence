from pydantic import BaseModel, ConfigDict


class CashFlowItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str
    current_year: float | None
    previous_year: float | None


class CashFlowData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: str
    reporting_date: str | None

    operating_activities: list[CashFlowItem]
    investing_activities: list[CashFlowItem]
    financing_activities: list[CashFlowItem]

    net_cash_from_operating_activities: float | None
    net_cash_from_investing_activities: float | None
    net_cash_from_financing_activities: float | None

    net_change_in_cash: float | None
    opening_cash_balance: float | None
    closing_cash_balance: float | None