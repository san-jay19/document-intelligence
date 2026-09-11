from pydantic import BaseModel, ConfigDict


class BalanceSheetData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: str
    reporting_date: str | None

    capital: float | None
    employee_stock_options: float | None
    reserves_and_surplus: float | None
    minority_interest: float | None
    deposits: float | None
    borrowings: float | None
    other_liabilities_and_provisions: float | None
    policyholders_funds: float | None

    total_liabilities: float | None

    cash_and_balances_with_rbi: float | None
    balances_with_banks: float | None
    investments: float | None
    advances: float | None
    fixed_assets: float | None
    other_assets: float | None

    total_assets: float | None

    contingent_liabilities: float | None
    bills_for_collection: float | None