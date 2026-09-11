from math import isclose

from backend.app.schemas.extraction import ExtractionResult


# =========================================================
# Helpers
# =========================================================

def _to_float(value):
    """
    Convert common AI/OCR number representations to float.

    Examples:

        1000
        1000.50
        "1000.50"
        "1,000.50"
        "$1,000.50"
        "10%"
        "(500)"
    """

    if value is None:
        return None

    if isinstance(
        value,
        (int, float),
    ):
        return float(value)

    if not isinstance(
        value,
        str,
    ):
        return None

    value = value.strip()

    if not value:
        return None

    # Parentheses represent negative values.
    negative = (
        value.startswith("(")
        and value.endswith(")")
    )

    value = (
        value.replace(",", "")
        .replace("$", "")
        .replace("€", "")
        .replace("£", "")
        .replace("₹", "")
        .replace("(", "")
        .replace(")", "")
        .strip()
    )

    if value.endswith("%"):
        value = value[:-1].strip()

    try:

        number = float(
            value
        )

        if negative:
            number = -number

        return number

    except ValueError:
        return None


def _get_field(
    extraction: ExtractionResult,
    field_name: str,
):
    """
    Find a field by normalized name.
    """

    target = (
        field_name
        .lower()
        .strip()
        .replace(" ", "_")
        .replace("-", "_")
    )

    for field in extraction.fields:

        current = (
            field.name
            .lower()
            .strip()
            .replace(" ", "_")
            .replace("-", "_")
        )

        if current == target:
            return field.value

    return None


def _find_field_by_names(
    extraction: ExtractionResult,
    names: list[str],
):
    """
    Find a field using multiple possible names.
    """

    normalized_names = {
        name.lower()
        .strip()
        .replace(" ", "_")
        .replace("-", "_")
        for name in names
    }

    for field in extraction.fields:

        current = (
            field.name
            .lower()
            .strip()
            .replace(" ", "_")
            .replace("-", "_")
        )

        if current in normalized_names:
            return field.value

    return None


def _find_line_item_table(
    extraction: ExtractionResult,
):
    """
    Find a likely line-item table.
    """

    if not extraction.tables:
        return None

    for table in extraction.tables:

        table_name = (
            table.table_name
            .lower()
        )

        if (
            "line" in table_name
            or "item" in table_name
            or "invoice" in table_name
        ):
            return table

    return extraction.tables[0]


def _find_header_index(
    headers: list[str],
    candidates: list[str],
):
    """
    Find a column index using possible header names.
    """

    normalized_headers = [
        header
        .lower()
        .strip()
        .replace(" ", "_")
        .replace("-", "_")
        for header in headers
    ]

    for candidate in candidates:

        candidate = (
            candidate
            .lower()
            .strip()
            .replace(" ", "_")
            .replace("-", "_")
        )

        if candidate in normalized_headers:
            return normalized_headers.index(
                candidate
            )

    return None


def _get_row_value(
    row,
    index,
):
    """
    Safely retrieve a value from a table row.
    """

    if index is None:
        return None

    if index >= len(row):
        return None

    return row[index]


# =========================================================
# Invoice Validation
# =========================================================

def _validate_invoice(
    extraction: ExtractionResult,
):
    errors = []
    warnings = []
    checks = []

    # -----------------------------------------------------
    # Find invoice-level fields
    # -----------------------------------------------------

    reported_vat = _to_float(
        _find_field_by_names(
            extraction,
            [
                "vat_amount",
                "vat",
                "tax_amount",
                "tax",
            ],
        )
    )

    reported_total = _to_float(
        _find_field_by_names(
            extraction,
            [
                "total_amount",
                "total",
                "gross_total",
                "grand_total",
            ],
        )
    )

    reported_subtotal = _to_float(
        _find_field_by_names(
            extraction,
            [
                "subtotal",
                "sub_total",
                "net_total",
                "net_amount",
            ],
        )
    )

    # -----------------------------------------------------
    # Find line items
    # -----------------------------------------------------

    table = _find_line_item_table(
        extraction
    )

    calculated_subtotal = 0.0
    calculated_vat = 0.0

    has_subtotal_calculation = False
    has_vat_calculation = False

    if table is None:

        warnings.append(
            "No invoice line-item table was found."
        )

    else:

        headers = table.headers

        if not headers:

            warnings.append(
                "Invoice table has no headers."
            )

        else:

            quantity_index = _find_header_index(
                headers,
                [
                    "quantity",
                    "qty",
                ],
            )

            unit_price_index = _find_header_index(
                headers,
                [
                    "unit_price",
                    "unit_price",
                    "net_price",
                    "price",
                ],
            )

            net_amount_index = _find_header_index(
                headers,
                [
                    "net_amount",
                    "net_worth",
                    "net_total",
                    "subtotal",
                    "amount",
                ],
            )

            vat_percent_index = _find_header_index(
                headers,
                [
                    "vat_percent",
                    "vat_percentage",
                    "vat_%",
                    "tax_percent",
                    "tax_percentage",
                ],
            )

            vat_amount_index = _find_header_index(
                headers,
                [
                    "vat_amount",
                    "tax_amount",
                    "vat_value",
                    "tax_value",
                ],
            )

            gross_amount_index = _find_header_index(
                headers,
                [
                    "gross_amount",
                    "gross_worth",
                    "gross_total",
                    "total",
                ],
            )

            # -------------------------------------------------
            # Process rows
            # -------------------------------------------------

            for row_number, row in enumerate(
                table.rows,
                start=1,
            ):

                quantity = _to_float(
                    _get_row_value(
                        row,
                        quantity_index,
                    )
                )

                unit_price = _to_float(
                    _get_row_value(
                        row,
                        unit_price_index,
                    )
                )

                net_amount = _to_float(
                    _get_row_value(
                        row,
                        net_amount_index,
                    )
                )

                vat_percent = _to_float(
                    _get_row_value(
                        row,
                        vat_percent_index,
                    )
                )

                row_vat_amount = _to_float(
                    _get_row_value(
                        row,
                        vat_amount_index,
                    )
                )

                gross_amount = _to_float(
                    _get_row_value(
                        row,
                        gross_amount_index,
                    )
                )

                # ---------------------------------------------
                # Quantity × Unit Price
                # ---------------------------------------------

                calculated_row_net = None

                if (
                    quantity is not None
                    and unit_price is not None
                ):

                    calculated_row_net = (
                        quantity * unit_price
                    )

                    if net_amount is not None:

                        variance = round(
                            calculated_row_net
                            - net_amount,
                            2,
                        )

                        status = (
                            "PASS"
                            if isclose(
                                calculated_row_net,
                                net_amount,
                                rel_tol=0.001,
                                abs_tol=0.01,
                            )
                            else "FAIL"
                        )

                        checks.append(
                            {
                                "name": (
                                    f"line_item_{row_number}"
                                    "_quantity_price_check"
                                ),

                                "formula": (
                                    "quantity × unit_price"
                                    " ≈ net_amount"
                                ),

                                "operands": {
                                    "quantity": quantity,
                                    "unit_price": unit_price,
                                },

                                "calculated_value": round(
                                    calculated_row_net,
                                    2,
                                ),

                                "reported_value": net_amount,

                                "variance": variance,

                                "status": status,
                            }
                        )

                        if status == "FAIL":
                            errors.append(
                                f"Line item {row_number}: "
                                "quantity × unit_price "
                                "does not match net amount."
                            )

                        has_subtotal_calculation = True

                elif net_amount is not None:

                    calculated_row_net = (
                        net_amount
                    )

                    has_subtotal_calculation = True

                # ---------------------------------------------
                # Add subtotal
                # ---------------------------------------------

                if calculated_row_net is not None:

                    calculated_subtotal += (
                        calculated_row_net
                    )

                # ---------------------------------------------
                # VAT calculation
                # ---------------------------------------------

                if (
                    net_amount is not None
                    and vat_percent is not None
                ):

                    calculated_row_vat = (
                        net_amount
                        * vat_percent
                        / 100
                    )

                    calculated_vat += (
                        calculated_row_vat
                    )

                    has_vat_calculation = True

                    if row_vat_amount is not None:

                        variance = round(
                            calculated_row_vat
                            - row_vat_amount,
                            2,
                        )

                        status = (
                            "PASS"
                            if isclose(
                                calculated_row_vat,
                                row_vat_amount,
                                rel_tol=0.001,
                                abs_tol=0.01,
                            )
                            else "FAIL"
                        )

                        checks.append(
                            {
                                "name": (
                                    f"line_item_{row_number}"
                                    "_vat_check"
                                ),

                                "formula": (
                                    "net_amount × "
                                    "vat_percent / 100 "
                                    "≈ vat_amount"
                                ),

                                "operands": {
                                    "net_amount": net_amount,
                                    "vat_percent": vat_percent,
                                },

                                "calculated_value": round(
                                    calculated_row_vat,
                                    2,
                                ),

                                "reported_value": (
                                    row_vat_amount
                                ),

                                "variance": variance,

                                "status": status,
                            }
                        )

                        if status == "FAIL":
                            errors.append(
                                f"Line item {row_number}: "
                                "VAT calculation does not "
                                "match reported VAT amount."
                            )

                elif row_vat_amount is not None:

                    calculated_vat += (
                        row_vat_amount
                    )

                    has_vat_calculation = True

                # gross_amount is captured for future
                # reconciliation but is not required
                # for this calculation.

                _ = gross_amount

    # -----------------------------------------------------
    # Subtotal validation
    # -----------------------------------------------------

    if reported_subtotal is not None:

        if has_subtotal_calculation:

            variance = round(
                calculated_subtotal
                - reported_subtotal,
                2,
            )

            status = (
                "PASS"
                if isclose(
                    calculated_subtotal,
                    reported_subtotal,
                    rel_tol=0.001,
                    abs_tol=0.01,
                )
                else "FAIL"
            )

            checks.append(
                {
                    "name": "invoice_subtotal_check",

                    "formula": (
                        "sum(line item net amounts)"
                        " ≈ reported subtotal"
                    ),

                    "operands": {
                        "calculated_subtotal": round(
                            calculated_subtotal,
                            2,
                        ),
                        "reported_subtotal": (
                            reported_subtotal
                        ),
                    },

                    "calculated_value": round(
                        calculated_subtotal,
                        2,
                    ),

                    "reported_value": reported_subtotal,

                    "variance": variance,

                    "status": status,
                }
            )

            if status == "FAIL":
                errors.append(
                    "Calculated subtotal does not "
                    "match reported subtotal."
                )

    # -----------------------------------------------------
    # VAT validation
    # -----------------------------------------------------

    if reported_vat is not None:

        if has_vat_calculation:

            variance = round(
                calculated_vat
                - reported_vat,
                2,
            )

            status = (
                "PASS"
                if isclose(
                    calculated_vat,
                    reported_vat,
                    rel_tol=0.001,
                    abs_tol=0.01,
                )
                else "FAIL"
            )

            checks.append(
                {
                    "name": "invoice_vat_check",

                    "formula": (
                        "sum(calculated VAT)"
                        " ≈ reported VAT"
                    ),

                    "operands": {
                        "calculated_vat": round(
                            calculated_vat,
                            2,
                        ),
                        "reported_vat": reported_vat,
                    },

                    "calculated_value": round(
                        calculated_vat,
                        2,
                    ),

                    "reported_value": reported_vat,

                    "variance": variance,

                    "status": status,
                }
            )

            if status == "FAIL":
                errors.append(
                    "Calculated VAT does not "
                    "match reported VAT."
                )

    # -----------------------------------------------------
    # Total validation
    # -----------------------------------------------------

    if reported_total is not None:

        if has_subtotal_calculation:

            # Prefer calculated VAT when available.
            if has_vat_calculation:

                calculated_total = (
                    calculated_subtotal
                    + calculated_vat
                )

                formula = (
                    "subtotal + VAT ≈ total"
                )

            elif reported_vat is not None:

                calculated_total = (
                    calculated_subtotal
                    + reported_vat
                )

                formula = (
                    "subtotal + reported VAT "
                    "≈ total"
                )

            else:

                calculated_total = None
                formula = None

            if calculated_total is not None:

                variance = round(
                    calculated_total
                    - reported_total,
                    2,
                )

                status = (
                    "PASS"
                    if isclose(
                        calculated_total,
                        reported_total,
                        rel_tol=0.001,
                        abs_tol=0.01,
                    )
                    else "FAIL"
                )

                checks.append(
                    {
                        "name": "invoice_total_check",

                        "formula": formula,

                        "operands": {
                            "calculated_subtotal": round(
                                calculated_subtotal,
                                2,
                            ),
                            "vat": (
                                round(
                                    calculated_vat,
                                    2,
                                )
                                if has_vat_calculation
                                else reported_vat
                            ),
                        },

                        "calculated_value": round(
                            calculated_total,
                            2,
                        ),

                        "reported_value": reported_total,

                        "variance": variance,

                        "status": status,
                    }
                )

                if status == "FAIL":
                    errors.append(
                        "Calculated total does not "
                        "match reported total."
                    )

    # -----------------------------------------------------
    # Determine overall status
    # -----------------------------------------------------

    if errors:
        overall_status = "FAIL"

    elif warnings:
        overall_status = "WARNING"

    elif not checks:
        overall_status = "NOT_APPLICABLE"

        warnings.append(
            "No applicable invoice financial checks "
            "could be performed."
        )

    else:
        overall_status = "PASS"

    return {
        "overall_status": overall_status,

        "checks": checks,

        "errors": errors,

        "warnings": warnings,

        "calculated_subtotal": round(
            calculated_subtotal,
            2,
        ),

        "calculated_vat": round(
            calculated_vat,
            2,
        ),

        "calculated_total": (
            round(
                calculated_subtotal
                + calculated_vat,
                2,
            )
            if has_subtotal_calculation
            else None
        ),
    }


# =========================================================
# Main Validation Router
# =========================================================

def validate_document_financials(
    extraction: ExtractionResult,
    document_type: str,
):
    """
    Route financial validation according to document type.

    Currently invoice validation is implemented.
    The other three document types will be added next.
    """

    document_type = (
        document_type
        .strip()
        .lower()
    )

    if document_type == "invoice":

        return _validate_invoice(
            extraction
        )

    return {
        "overall_status": "NOT_APPLICABLE",

        "checks": [],

        "errors": [],

        "warnings": [
            (
                f"Financial validation for "
                f"'{document_type}' is not "
                "implemented yet."
            )
        ],
    }