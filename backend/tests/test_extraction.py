from backend.app.services.extraction_service import (
    extract_document_data,
)


sample_text = """
INVOICE

Invoice Number: INV-1001
Issue Date: 2026-08-15

Seller:
ABC Technologies

Client:
XYZ Ltd

Description        Quantity    Net Price    Net Worth    VAT    Gross Worth
Laptop Computer    2           500.00       1000.00      10%    1100.00

VAT Amount: 100.00
Total Amount: 1100.00
"""


result = extract_document_data(
    document_text=sample_text,
    document_type="invoice",
)


print(result.model_dump_json(indent=2))