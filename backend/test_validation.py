from backend.app.schemas.extraction import (
    ExtractedField,
    ExtractedTable,
    ExtractionResult,
)

from backend.app.services.financial_validation_service import (
    validate_document_financials,
)


extraction = ExtractionResult(
    document_type="invoice",

    fields=[
        ExtractedField(
            name="vat_amount",
            value=100.0,
            evidence="VAT Amount: 100.00",
            confidence=0.99,
        ),

        ExtractedField(
            name="total_amount",
            value=1100.0,
            evidence="Total Amount: 1100.00",
            confidence=0.99,
        ),
    ],

    tables=[
        ExtractedTable(
            table_name="Line Items",

            headers=[
                "description",
                "quantity",
                "unit_price",
                "net_amount",
                "vat_percent",
                "gross_amount",
            ],

            rows=[
                [
                    "Laptop Computer",
                    2,
                    500.0,
                    1000.0,
                    "10%",
                    "1100.0",
                ]
            ],
        )
    ],
)


result = validate_document_financials(
    extraction=extraction,
    document_type="invoice",
)


print(result)