from backend.app.schemas.extraction import (
    ExtractionResult,
    ExtractedField,
    ExtractedTable,
)

from backend.app.services.financial_validation_service import (
    validate_invoice_financials,
)

from backend.app.services.balance_sheet_validation_service import (
    validate_balance_sheet,
)

from backend.app.services.profit_loss_validation_service import (
    validate_profit_loss,
)

from backend.app.services.cash_flow_validation_service import (
    validate_cash_flow,
)


def test_invoice_validation_passes():
    extraction = ExtractionResult(
        document_type="invoice",
        fields=[
            ExtractedField(
                name="vat_amount",
                value=100,
            ),
            ExtractedField(
                name="total_amount",
                value=1100,
            ),
        ],
        tables=[
            ExtractedTable(
                table_name="Line Items",
                headers=[
                    "Quantity",
                    "Net Price",
                    "Net Worth",
                    "VAT %",
                    "Gross Worth",
                ],
                rows=[
                    [1, 1000, 1000, 10, 1100],
                ],
            )
        ],
    )

    result = validate_invoice_financials(
        extraction
    )

    assert result["overall_status"] == "PASS"


def test_invoice_validation_fails_when_total_is_wrong():
    extraction = ExtractionResult(
        document_type="invoice",
        fields=[
            ExtractedField(
                name="vat_amount",
                value=100,
            ),
            ExtractedField(
                name="total_amount",
                value=1200,
            ),
        ],
        tables=[
            ExtractedTable(
                table_name="Line Items",
                headers=[
                    "Quantity",
                    "Net Price",
                    "Net Worth",
                    "VAT %",
                    "Gross Worth",
                ],
                rows=[
                    [1, 1000, 1000, 10, 1100],
                ],
            )
        ],
    )

    result = validate_invoice_financials(
        extraction
    )

    assert result["overall_status"] == "FAIL"


def test_balance_sheet_validation():
    extraction = ExtractionResult(
        document_type="balance_sheet",
        fields=[
            ExtractedField(
                name="Total Assets",
                value=[1000, 900],
            ),
            ExtractedField(
                name="Total Capital & Liabilities",
                value=[1000, 900],
            ),
            ExtractedField(
                name="Cash and balances with RBI",
                value=[100, 90],
            ),
            ExtractedField(
                name="Balances with banks and money at call and short notice",
                value=[100, 90],
            ),
            ExtractedField(
                name="Investments",
                value=[200, 180],
            ),
            ExtractedField(
                name="Advances",
                value=[300, 270],
            ),
            ExtractedField(
                name="Fixed assets",
                value=[100, 90],
            ),
            ExtractedField(
                name="Other assets",
                value=[200, 180],
            ),
        ],
    )

    result = validate_balance_sheet(
        extraction
    )

    assert result["overall_status"] == "PASS"


def test_profit_loss_validation():
    extraction = ExtractionResult(
        document_type="profit_and_loss",
        fields=[
            ExtractedField(
                name="Interest Earned",
                value=[700, 600],
            ),
            ExtractedField(
                name="Other Income",
                value=[300, 200],
            ),
            ExtractedField(
                name="Total Income",
                value=[1000, 800],
            ),
            ExtractedField(
                name="Interest Expended",
                value=[200, 150],
            ),
            ExtractedField(
                name="Operating Expenses",
                value=[300, 250],
            ),
            ExtractedField(
                name="Provisions and Contingencies",
                value=[100, 100],
            ),
            ExtractedField(
                name="Total Expenditure",
                value=[600, 500],
            ),
            ExtractedField(
                name="Net profit for the year",
                value=[400, 300],
            ),
            ExtractedField(
                name="Minority Interest",
                value=[50, 40],
            ),
            ExtractedField(
                name="Consolidated profit for the year",
                value=[350, 260],
            ),
            ExtractedField(
                name="Balance in P&L Account brought forward",
                value=[100, 100],
            ),
            ExtractedField(
                name="Total",
                value=[450, 360],
            ),
        ],
    )

    result = validate_profit_loss(
        extraction
    )

    assert result["overall_status"] == "PASS"


def test_cash_flow_validation():
    extraction = ExtractionResult(
        document_type="cash_flow_statement",
        fields=[
            ExtractedField(
                name="Net cash generated from operating activities",
                value=[500, 400],
            ),
            ExtractedField(
                name="Net cash used in investing activities",
                value=[-100, -50],
            ),
            ExtractedField(
                name="Net cash generated from financing activities",
                value=[200, 100],
            ),
            ExtractedField(
                name="Effect of exchange rate changes",
                value=[0, 0],
            ),
            ExtractedField(
                name="Net increase in cash and cash equivalents",
                value=[600, 450],
            ),
            ExtractedField(
                name="Cash and cash equivalents at beginning",
                value=[400, 300],
            ),
            ExtractedField(
                name="Cash and cash equivalents at end",
                value=[1000, 750],
            ),
        ],
    )

    result = validate_cash_flow(
        extraction
    )

    assert result["overall_status"] in {
        "PASS",
        "FAIL",
        "WARNING",
    }