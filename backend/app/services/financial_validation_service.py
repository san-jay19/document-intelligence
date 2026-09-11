from math import isclose


# =========================================================
# Helpers
# =========================================================

def _to_float(value):
    """
    Convert an extracted value into a float.

    Supports:
        1000
        1000.50
        "1000"
        "1,000.50"
        "$1,000.50"
        "10%"
    """

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return None

        value = (
            value.replace(",", "")
            .replace("$", "")
            .replace("€", "")
            .replace("£", "")
            .replace("₹", "")
            .strip()
        )

        if value.endswith("%"):
            value = value[:-1].strip()

        try:
            return float(value)
        except ValueError:
            return None

    return None


def _get_field_value(extraction, field_name):
    """
    Find a field by normalized field name.
    """

    target = field_name.lower().strip()

    for field in extraction.fields:
        name = str(field.name).lower().strip()

        if name == target:
            return field.value

    return None


def _find_line_items_table(extraction):
    """
    Find the line-item table.

    Prefer a table whose name contains "line" or "item".
    Otherwise use the first available table.
    """

    if not extraction.tables:
        return None

    for table in extraction.tables:
        table_name = (
            str(table.table_name)
            .lower()
            .strip()
        )

        if "line" in table_name or "item" in table_name:
            return table

    return extraction.tables[0]


def _header_index(headers, possible_names):
    """
    Find a column index using a list of possible header names.
    """

    normalized_headers = [
        str(header).lower().strip()
        for header in headers
    ]

    for possible_name in possible_names:
        target = possible_name.lower().strip()

        if target in normalized_headers:
            return normalized_headers.index(target)

    return None


def _make_check(
    name,
    status,
    calculated=None,
    reported=None,
    variance=None,
    formula=None,
):
    """
    Build one standardized validation check.
    """

    check = {
        "check": name,
        "status": status,
        "calculated": calculated,
        "reported": reported,
    }

    if variance is not None:
        check["variance"] = variance

    if formula is not None:
        check["formula"] = formula

    return check


# =========================================================
# Invoice Financial Validation
# =========================================================

def validate_invoice_financials(extraction):
    """
    Validate Invoice financial calculations.

    Checks:

        1. Quantity × Unit Price ≈ Net Amount
        2. Net Amount × VAT % ≈ VAT Amount
        3. Net Amount + VAT ≈ Gross Amount
        4. Sum of line VAT ≈ Invoice VAT
        5. Subtotal + VAT ≈ Invoice Total

    Missing values are not invented.
    """

    errors = []
    warnings = []
    checks = []

    calculated_subtotal = 0.0
    calculated_vat = 0.0

    # =====================================================
    # Invoice-level values
    # =====================================================

    vat_amount = _to_float(
        _get_field_value(
            extraction,
            "vat_amount",
        )
    )

    if vat_amount is None:
        vat_amount = _to_float(
            _get_field_value(
                extraction,
                "tax_amount",
            )
        )

    total_amount = _to_float(
        _get_field_value(
            extraction,
            "total_amount",
        )
    )

    if total_amount is None:
        total_amount = _to_float(
            _get_field_value(
                extraction,
                "total",
            )
        )

    # =====================================================
    # Find line-item table
    # =====================================================

    table = _find_line_items_table(extraction)

    if table is None:

        warnings.append(
            "No line-item table was found."
        )

    else:

        headers = table.headers or []

        if not headers:

            warnings.append(
                "Line-item table has no headers."
            )

        else:

            # -------------------------------------------------
            # Column indexes
            # -------------------------------------------------

            quantity_index = _header_index(
                headers,
                [
                    "quantity",
                    "qty",
                ],
            )

            unit_price_index = _header_index(
                headers,
                [
                    "unit_price",
                    "unit price",
                    "net_price",
                    "net price",
                    "price",
                ],
            )

            net_amount_index = _header_index(
                headers,
                [
                    "net_amount",
                    "net amount",
                    "net_worth",
                    "net worth",
                    "subtotal",
                ],
            )

            vat_percent_index = _header_index(
                headers,
                [
                    "vat_percent",
                    "vat percent",
                    "vat %",
                    "vat[%]",
                    "tax_percent",
                    "tax %",
                ],
            )

            vat_amount_index = _header_index(
                headers,
                [
                    "vat_amount",
                    "vat amount",
                    "tax_amount",
                    "tax amount",
                ],
            )

            gross_amount_index = _header_index(
                headers,
                [
                    "gross_amount",
                    "gross amount",
                    "gross_worth",
                    "gross worth",
                    "total",
                ],
            )

            # -------------------------------------------------
            # Process line items
            # -------------------------------------------------

            for row_index, row in enumerate(table.rows):

                def get_value(column_index):
                    if column_index is None:
                        return None

                    if column_index >= len(row):
                        return None

                    return row[column_index]

                quantity = _to_float(
                    get_value(quantity_index)
                )

                unit_price = _to_float(
                    get_value(unit_price_index)
                )

                net_amount = _to_float(
                    get_value(net_amount_index)
                )

                vat_percent = _to_float(
                    get_value(vat_percent_index)
                )

                row_vat_amount = _to_float(
                    get_value(vat_amount_index)
                )

                gross_amount = _to_float(
                    get_value(gross_amount_index)
                )

                # =================================================
                # Quantity × Unit Price ≈ Net Amount
                # =================================================

                if (
                    quantity is not None
                    and unit_price is not None
                ):

                    calculated_net = (
                        quantity * unit_price
                    )

                    if net_amount is not None:

                        variance = (
                            calculated_net
                            - net_amount
                        )

                        status = (
                            "PASS"
                            if isclose(
                                calculated_net,
                                net_amount,
                                rel_tol=0.001,
                                abs_tol=0.01,
                            )
                            else "FAIL"
                        )

                        checks.append(
                            _make_check(
                                name=(
                                    f"Item {row_index + 1}: "
                                    "quantity × unit price ≈ "
                                    "net amount"
                                ),
                                formula=(
                                    "quantity × unit_price"
                                ),
                                calculated=round(
                                    calculated_net,
                                    2,
                                ),
                                reported=round(
                                    net_amount,
                                    2,
                                ),
                                variance=round(
                                    variance,
                                    2,
                                ),
                                status=status,
                            )
                        )

                        if status == "FAIL":
                            errors.append(
                                f"Item {row_index + 1}: "
                                "quantity × unit price does not "
                                "match net amount."
                            )

                    else:

                        checks.append(
                            _make_check(
                                name=(
                                    f"Item {row_index + 1}: "
                                    "quantity × unit price"
                                ),
                                formula=(
                                    "quantity × unit_price"
                                ),
                                calculated=round(
                                    calculated_net,
                                    2,
                                ),
                                reported=None,
                                status="NOT_APPLICABLE",
                            )
                        )

                    calculated_subtotal += (
                        calculated_net
                    )

                elif net_amount is not None:

                    calculated_subtotal += (
                        net_amount
                    )

                    checks.append(
                        _make_check(
                            name=(
                                f"Item {row_index + 1}: "
                                "reported net amount"
                            ),
                            formula="reported net amount",
                            calculated=round(
                                net_amount,
                                2,
                            ),
                            reported=round(
                                net_amount,
                                2,
                            ),
                            variance=0.0,
                            status="PASS",
                        )
                    )

                else:

                    warnings.append(
                        f"Item {row_index + 1}: "
                        "insufficient financial data to "
                        "calculate net amount."
                    )

                    checks.append(
                        _make_check(
                            name=(
                                f"Item {row_index + 1}: "
                                "net amount validation"
                            ),
                            formula=(
                                "quantity × unit_price ≈ "
                                "net_amount"
                            ),
                            status="NOT_APPLICABLE",
                        )
                    )

                # =================================================
                # Net Amount × VAT % ≈ VAT Amount
                # =================================================

                if (
                    net_amount is not None
                    and vat_percent is not None
                ):

                    calculated_row_vat = (
                        net_amount
                        * vat_percent
                        / 100
                    )

                    if row_vat_amount is not None:

                        variance = (
                            calculated_row_vat
                            - row_vat_amount
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
                            _make_check(
                                name=(
                                    f"Item {row_index + 1}: "
                                    "net amount × VAT % ≈ "
                                    "VAT amount"
                                ),
                                formula=(
                                    "net_amount × vat_percent / 100"
                                ),
                                calculated=round(
                                    calculated_row_vat,
                                    2,
                                ),
                                reported=round(
                                    row_vat_amount,
                                    2,
                                ),
                                variance=round(
                                    variance,
                                    2,
                                ),
                                status=status,
                            )
                        )

                        if status == "FAIL":
                            errors.append(
                                f"Item {row_index + 1}: "
                                "net amount × VAT % does not "
                                "match VAT amount."
                            )

                    else:

                        checks.append(
                            _make_check(
                                name=(
                                    f"Item {row_index + 1}: "
                                    "VAT calculation"
                                ),
                                formula=(
                                    "net_amount × vat_percent / 100"
                                ),
                                calculated=round(
                                    calculated_row_vat,
                                    2,
                                ),
                                reported=None,
                                status="NOT_APPLICABLE",
                            )
                        )

                    calculated_vat += (
                        calculated_row_vat
                    )

                elif row_vat_amount is not None:

                    calculated_vat += (
                        row_vat_amount
                    )

                    checks.append(
                        _make_check(
                            name=(
                                f"Item {row_index + 1}: "
                                "reported VAT amount"
                            ),
                            formula="reported VAT amount",
                            calculated=round(
                                row_vat_amount,
                                2,
                            ),
                            reported=round(
                                row_vat_amount,
                                2,
                            ),
                            variance=0.0,
                            status="PASS",
                        )
                    )

                else:

                    checks.append(
                        _make_check(
                            name=(
                                f"Item {row_index + 1}: "
                                "VAT validation"
                            ),
                            formula=(
                                "net_amount × vat_percent / 100 "
                                "≈ vat_amount"
                            ),
                            status="NOT_APPLICABLE",
                        )
                    )

                # =================================================
                # Net + VAT ≈ Gross
                # =================================================

                if gross_amount is not None:

                    expected_gross = None

                    if (
                        net_amount is not None
                        and row_vat_amount is not None
                    ):
                        expected_gross = (
                            net_amount
                            + row_vat_amount
                        )

                    elif (
                        net_amount is not None
                        and vat_percent is not None
                    ):
                        expected_gross = (
                            net_amount
                            + (
                                net_amount
                                * vat_percent
                                / 100
                            )
                        )

                    if expected_gross is not None:

                        variance = (
                            expected_gross
                            - gross_amount
                        )

                        status = (
                            "PASS"
                            if isclose(
                                expected_gross,
                                gross_amount,
                                rel_tol=0.001,
                                abs_tol=0.01,
                            )
                            else "FAIL"
                        )

                        checks.append(
                            _make_check(
                                name=(
                                    f"Item {row_index + 1}: "
                                    "net + VAT ≈ gross"
                                ),
                                formula=(
                                    "net_amount + vat_amount"
                                ),
                                calculated=round(
                                    expected_gross,
                                    2,
                                ),
                                reported=round(
                                    gross_amount,
                                    2,
                                ),
                                variance=round(
                                    variance,
                                    2,
                                ),
                                status=status,
                            )
                        )

                        if status == "FAIL":
                            errors.append(
                                f"Item {row_index + 1}: "
                                "net + VAT does not match "
                                "gross amount."
                            )

    # =====================================================
    # Invoice VAT reconciliation
    # =====================================================

    if vat_amount is not None:

        variance = (
            calculated_vat
            - vat_amount
        )

        status = (
            "PASS"
            if isclose(
                calculated_vat,
                vat_amount,
                rel_tol=0.001,
                abs_tol=0.01,
            )
            else "FAIL"
        )

        checks.append(
            _make_check(
                name="Calculated VAT ≈ invoice VAT",
                formula="sum(line VAT amounts)",
                calculated=round(
                    calculated_vat,
                    2,
                ),
                reported=round(
                    vat_amount,
                    2,
                ),
                variance=round(
                    variance,
                    2,
                ),
                status=status,
            )
        )

        if status == "FAIL":
            errors.append(
                "Calculated VAT does not match "
                "invoice VAT amount."
            )

    else:

        warnings.append(
            "Invoice VAT amount was not found."
        )

        checks.append(
            _make_check(
                name="Calculated VAT ≈ invoice VAT",
                formula="sum(line VAT amounts)",
                calculated=round(
                    calculated_vat,
                    2,
                ),
                reported=None,
                status="NOT_APPLICABLE",
            )
        )

    # =====================================================
    # Subtotal + VAT ≈ Total
    # =====================================================

    calculated_total = (
        calculated_subtotal
        + calculated_vat
    )

    if total_amount is not None:

        variance = (
            calculated_total
            - total_amount
        )

        status = (
            "PASS"
            if isclose(
                calculated_total,
                total_amount,
                rel_tol=0.001,
                abs_tol=0.01,
            )
            else "FAIL"
        )

        checks.append(
            _make_check(
                name="Subtotal + VAT ≈ total",
                formula="subtotal + VAT",
                calculated=round(
                    calculated_total,
                    2,
                ),
                reported=round(
                    total_amount,
                    2,
                ),
                variance=round(
                    variance,
                    2,
                ),
                status=status,
            )
        )

        if status == "FAIL":
            errors.append(
                "Subtotal + VAT does not match "
                "invoice total."
            )

    else:

        warnings.append(
            "Invoice total amount was not found."
        )

        checks.append(
            _make_check(
                name="Subtotal + VAT ≈ total",
                formula="subtotal + VAT",
                calculated=round(
                    calculated_total,
                    2,
                ),
                reported=None,
                status="NOT_APPLICABLE",
            )
        )

    # =====================================================
    # Overall Status
    # =====================================================

    if errors:
        overall_status = "FAIL"

    elif warnings:
        overall_status = "WARNING"

    else:
        overall_status = "PASS"

    # =====================================================
    # Summary
    # =====================================================

    passed_checks = sum(
        1
        for check in checks
        if check.get("status") == "PASS"
    )

    failed_checks = sum(
        1
        for check in checks
        if check.get("status") == "FAIL"
    )

    not_applicable_checks = sum(
        1
        for check in checks
        if check.get("status") == "NOT_APPLICABLE"
    )

    # =====================================================
    # Final Result
    # =====================================================

    return {
        "status": overall_status,
        "overall_status": overall_status,

        "checks": checks,

        "calculated_subtotal": round(
            calculated_subtotal,
            2,
        ),

        "calculated_vat": round(
            calculated_vat,
            2,
        ),

        "calculated_total": round(
            calculated_total,
            2,
        ),

        "errors": errors,

        "warnings": warnings,

        "summary": {
            "periods_checked": 1,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "not_applicable_checks": not_applicable_checks,
        },
    }