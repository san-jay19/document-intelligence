# =========================================================
# Validation Router
# =========================================================
#
# Routes each supported document type to its corresponding
# financial validation service.
#
# Supported:
#   - invoice
#   - balance_sheet
#   - profit_and_loss
#   - cash_flow_statement
#
# The router also normalizes the older Invoice validator
# response so that main.py receives one consistent structure.
# =========================================================


from backend.app.schemas.extraction import ExtractionResult


# ---------------------------------------------------------
# Invoice validator
# ---------------------------------------------------------

try:
    from backend.app.services.financial_validation_service import (
        validate_invoice_financials,
    )
except ImportError:
    validate_invoice_financials = None


# ---------------------------------------------------------
# Balance Sheet validator
# ---------------------------------------------------------

try:
    from backend.app.services.balance_sheet_validation_service import (
        validate_balance_sheet,
    )
except ImportError:
    validate_balance_sheet = None


# ---------------------------------------------------------
# Profit & Loss validator
# ---------------------------------------------------------

try:
    from backend.app.services.profit_loss_validation_service import (
        validate_profit_loss,
    )
except ImportError:
    validate_profit_loss = None


# ---------------------------------------------------------
# Cash Flow validator
# ---------------------------------------------------------

try:
    from backend.app.services.cash_flow_validation_service import (
        validate_cash_flow,
    )
except ImportError:
    validate_cash_flow = None


# =========================================================
# Helper: normalize invoice result
# =========================================================

def _normalize_invoice_result(result: dict) -> dict:
    """
    Convert the existing Invoice validator response
    into the common validation response structure
    expected by main.py.

    Existing Invoice validator may return:

        {
            "status": "PASS",
            "calculated_subtotal": ...,
            "calculated_vat": ...,
            "calculated_total": ...,
            "errors": [...],
            "warnings": [...]
        }

    The API expects:

        {
            "overall_status": "PASS",
            ...
        }
    """

    if not isinstance(result, dict):
        return {
            "overall_status": "FAIL",
            "checks": [],
            "errors": [
                "Invoice validator returned an invalid response."
            ],
            "warnings": [],
            "summary": {
                "periods_checked": 0,
                "passed_checks": 0,
                "failed_checks": 1,
                "not_applicable_checks": 0,
            },
        }

    status = result.get("status")

    if status == "PASS":
        overall_status = "PASS"

    elif status == "WARNING":
        overall_status = "WARNING"

    elif status == "FAIL":
        overall_status = "FAIL"

    else:
        overall_status = "NOT_APPLICABLE"

    errors = result.get("errors", [])
    warnings = result.get("warnings", [])

    # Create a compact validation check entry for Invoice.
    checks = []

    calculated_subtotal = result.get(
        "calculated_subtotal"
    )

    calculated_vat = result.get(
        "calculated_vat"
    )

    calculated_total = result.get(
        "calculated_total"
    )

    checks.append(
        {
            "check": "Invoice financial reconciliation",
            "status": overall_status,
            "calculated_subtotal": calculated_subtotal,
            "calculated_vat": calculated_vat,
            "calculated_total": calculated_total,
        }
    )

    return {
        "overall_status": overall_status,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "periods_checked": 1,
            "passed_checks": (
                1 if overall_status == "PASS" else 0
            ),
            "failed_checks": (
                1 if overall_status == "FAIL" else 0
            ),
            "not_applicable_checks": (
                1
                if overall_status == "NOT_APPLICABLE"
                else 0
            ),
        },

        # Preserve the original Invoice validator values.
        "calculated_subtotal": calculated_subtotal,
        "calculated_vat": calculated_vat,
        "calculated_total": calculated_total,
    }


# =========================================================
# Helper: normalize generic validator result
# =========================================================

def _normalize_generic_result(result: dict) -> dict:
    """
    Ensure that a validator response always has the fields
    expected by main.py.
    """

    if not isinstance(result, dict):
        return {
            "overall_status": "FAIL",
            "checks": [],
            "errors": [
                "Validator returned an invalid response."
            ],
            "warnings": [],
            "summary": {
                "periods_checked": 0,
                "passed_checks": 0,
                "failed_checks": 1,
                "not_applicable_checks": 0,
            },
        }

    # Some validators may already use overall_status.
    if "overall_status" not in result:

        # Fall back to "status" when present.
        if "status" in result:
            result["overall_status"] = result["status"]

        else:
            result["overall_status"] = "NOT_APPLICABLE"

    result.setdefault("checks", [])
    result.setdefault("errors", [])
    result.setdefault("warnings", [])

    result.setdefault(
        "summary",
        {
            "periods_checked": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "not_applicable_checks": 0,
        },
    )

    return result


# =========================================================
# Main validation router
# =========================================================

def validate_document_financials(
    extraction: ExtractionResult,
    document_type: str,
) -> dict:
    """
    Route the extracted document to the correct
    financial validator.

    Parameters
    ----------
    extraction:
        Generic ExtractionResult containing fields/tables.

    document_type:
        One of:

            invoice
            balance_sheet
            profit_and_loss
            cash_flow_statement

    Returns
    -------
    dict
        Consistent financial validation response.
    """

    normalized_type = (
        document_type
        .strip()
        .lower()
    )

    # -----------------------------------------------------
    # Invoice
    # -----------------------------------------------------

    if normalized_type == "invoice":

        if validate_invoice_financials is None:
            return {
                "overall_status": "NOT_APPLICABLE",
                "checks": [],
                "errors": [],
                "warnings": [
                    (
                        "Invoice validation service could not "
                        "be imported."
                    )
                ],
                "summary": {
                    "periods_checked": 0,
                    "passed_checks": 0,
                    "failed_checks": 0,
                    "not_applicable_checks": 1,
                },
            }

        result = validate_invoice_financials(
            extraction
        )

        return _normalize_invoice_result(result)

    # -----------------------------------------------------
    # Balance Sheet
    # -----------------------------------------------------

    if normalized_type == "balance_sheet":

        if validate_balance_sheet is None:
            return {
                "overall_status": "NOT_APPLICABLE",
                "checks": [],
                "errors": [],
                "warnings": [
                    (
                        "Balance Sheet validation service "
                        "could not be imported."
                    )
                ],
                "summary": {
                    "periods_checked": 0,
                    "passed_checks": 0,
                    "failed_checks": 0,
                    "not_applicable_checks": 1,
                },
            }

        result = validate_balance_sheet(
            extraction
        )

        return _normalize_generic_result(result)

    # -----------------------------------------------------
    # Profit & Loss
    # -----------------------------------------------------

    if normalized_type == "profit_and_loss":

        if validate_profit_loss is None:
            return {
                "overall_status": "NOT_APPLICABLE",
                "checks": [],
                "errors": [],
                "warnings": [
                    (
                        "Profit & Loss validation service "
                        "could not be imported."
                    )
                ],
                "summary": {
                    "periods_checked": 0,
                    "passed_checks": 0,
                    "failed_checks": 0,
                    "not_applicable_checks": 1,
                },
            }

        result = validate_profit_loss(
            extraction
        )

        return _normalize_generic_result(result)

    # -----------------------------------------------------
    # Cash Flow Statement
    # -----------------------------------------------------

    if normalized_type == "cash_flow_statement":

        if validate_cash_flow is None:
            return {
                "overall_status": "NOT_APPLICABLE",
                "checks": [],
                "errors": [],
                "warnings": [
                    (
                        "Cash Flow validation service "
                        "could not be imported."
                    )
                ],
                "summary": {
                    "periods_checked": 0,
                    "passed_checks": 0,
                    "failed_checks": 0,
                    "not_applicable_checks": 1,
                },
            }

        result = validate_cash_flow(
            extraction
        )

        return _normalize_generic_result(result)

    # -----------------------------------------------------
    # Unsupported document type
    # -----------------------------------------------------

    return {
        "overall_status": "NOT_APPLICABLE",
        "checks": [],
        "errors": [],
        "warnings": [
            (
                f"Financial validation is not implemented "
                f"for document type '{document_type}'."
            )
        ],
        "summary": {
            "periods_checked": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "not_applicable_checks": 1,
        },
    }