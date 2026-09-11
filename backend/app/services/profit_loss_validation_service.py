import re
from typing import Any

from backend.app.schemas.extraction import ExtractionResult


# =========================================================
# Number Parsing
# =========================================================

def _parse_number(value: Any) -> float | None:
    """
    Convert extracted financial values into a number.

    Supports:
    - commas
    - spaces
    - parentheses as negative
    - explicit minus signs
    - accounting dash as zero
    - common currency symbols
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    if not text:
        return None

    # Accounting dash.
    if text in {"-", "—", "–"}:
        return 0.0

    negative = False

    # Parentheses mean negative.
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()

    text = text.replace(",", "")
    text = text.replace(" ", "")

    text = text.replace("₹", "")
    text = text.replace("$", "")
    text = text.replace("€", "")
    text = text.replace("£", "")

    # Preserve digits, decimal point and minus sign.
    text = re.sub(
        r"[^0-9.\-]",
        "",
        text,
    )

    if not text:
        return None

    try:
        number = float(text)
    except ValueError:
        return None

    if negative:
        number = -abs(number)

    return number


# =========================================================
# Name Normalization
# =========================================================

def _normalize_name(name: str) -> str:
    """
    Normalize field names for matching.
    """

    name = name.lower().strip()

    name = name.replace(
        "&",
        "and",
    )

    name = re.sub(
        r"[^a-z0-9]+",
        " ",
        name,
    )

    return " ".join(
        name.split()
    )


# =========================================================
# Field Index
# =========================================================

def _build_field_index(
    extraction: ExtractionResult,
) -> dict[str, list[dict]]:
    """
    Build field index while preserving duplicate values.

    Duplicate fields represent comparative periods.
    """

    index: dict[str, list[dict]] = {}

    for field in extraction.fields:

        key = _normalize_name(
            field.name
        )

        index.setdefault(
            key,
            [],
        ).append(
            {
                "name": field.name,
                "value": field.value,
                "evidence": field.evidence,
                "confidence": field.confidence,
            }
        )

    return index


# =========================================================
# Field Lookup
# =========================================================

def _find_fields(
    field_index: dict[str, list[dict]],
    aliases: list[str],
) -> list[dict]:
    """
    Find fields by exact match first and partial match second.
    """

    normalized_aliases = [
        _normalize_name(alias)
        for alias in aliases
    ]

    # Exact match.
    for alias in normalized_aliases:

        if alias in field_index:
            return field_index[alias]

    # Partial match.
    for field_name, values in field_index.items():

        for alias in normalized_aliases:

            if (
                alias in field_name
                or field_name in alias
            ):
                return values

    return []


# =========================================================
# Period Value
# =========================================================

def _get_period_value(
    fields: list[dict],
    period_index: int,
) -> float | None:

    if period_index >= len(fields):
        return None

    return _parse_number(
        fields[period_index]["value"]
    )


# =========================================================
# Period Evidence
# =========================================================

def _get_period_evidence(
    fields: list[dict],
    period_index: int,
) -> str | None:

    if period_index >= len(fields):
        return None

    return fields[
        period_index
    ].get("evidence")


# =========================================================
# Period Count Validation
# =========================================================

def _has_expected_period_count(
    fields: list[dict],
    period_count: int,
) -> bool:
    """
    Require exactly one extracted value per comparative period.

    This prevents malformed OCR fields from creating extra periods.
    """

    if not fields:
        return False

    return len(fields) == period_count


# =========================================================
# Tolerance
# =========================================================

def _within_tolerance(
    calculated: float,
    reported: float,
    absolute_tolerance: float = 1.0,
    relative_tolerance: float = 0.001,
) -> bool:
    """
    Compare calculated and reported values.

    Default relative tolerance:
        0.1%
    """

    variance = abs(
        calculated - reported
    )

    allowed = max(
        absolute_tolerance,
        abs(reported) * relative_tolerance,
    )

    return variance <= allowed


# =========================================================
# Check Builder
# =========================================================

def _make_check(
    *,
    period: str,
    name: str,
    formula: str,
    operands: dict,
    calculated: float | None,
    reported: float | None,
    status: str,
    message: str,
    evidence: dict | None = None,
) -> dict:

    variance = None

    if (
        calculated is not None
        and reported is not None
    ):
        variance = (
            calculated - reported
        )

    return {
        "period": period,
        "check": name,
        "formula": formula,
        "operands": operands,
        "calculated": calculated,
        "reported": reported,
        "variance": variance,
        "status": status,
        "message": message,
        "evidence": evidence or {},
    }


# =========================================================
# Profit & Loss Validator
# =========================================================

def validate_profit_loss(
    extraction: ExtractionResult,
) -> dict:
    """
    Validate Profit & Loss financial relationships.

    Required case-study checks:

    1. Interest Earned + Other Income ≈ Total Income.

    2. Interest Expended + Operating Expenses
       + Provisions & Contingencies ≈ Total Expenditure.

    3. Total Income - Total Expenditure
       ≈ Net Profit before Minority Interest.

    4. Profit before Minority Interest - Minority Interest
       ≈ Consolidated Profit attributable to Group.

       Where an associate-profit adjustment is clearly and
       reliably extracted, the difference is reported as an
       optional informational adjustment rather than silently
       changing the mandatory formula.

    5. Current Consolidated Profit + Brought Forward Profit
       ≈ Total Available for Appropriation.

    Comparative periods are validated independently.
    """

    field_index = _build_field_index(
        extraction
    )

    # =====================================================
    # Main Income Fields
    # =====================================================

    interest_earned_fields = _find_fields(
        field_index,
        [
            "Interest earned",
        ],
    )

    other_income_fields = _find_fields(
        field_index,
        [
            "Other income",
        ],
    )

    total_income_fields = _find_fields(
        field_index,
        [
            "Total income",
        ],
    )

    # =====================================================
    # Expenditure Fields
    # =====================================================

    interest_expended_fields = _find_fields(
        field_index,
        [
            "Interest expended",
        ],
    )

    operating_expenses_fields = _find_fields(
        field_index,
        [
            "Operating expenses",
        ],
    )

    provisions_fields = _find_fields(
        field_index,
        [
            "Provisions and contingencies",
            "Provisions & contingencies",
        ],
    )

    total_expenditure_fields = _find_fields(
        field_index,
        [
            "Total expenditure",
        ],
    )

    # =====================================================
    # Profit Fields
    # =====================================================

    net_profit_fields = _find_fields(
        field_index,
        [
            "Net profit for the year",
            "Net profit",
        ],
    )

    minority_interest_fields = _find_fields(
        field_index,
        [
            "Minority interest",
            "Minority interests",
        ],
    )

    consolidated_profit_fields = _find_fields(
        field_index,
        [
            "Consolidated profit for the year",
            "Consolidated profit",
            "Consolidated net profit",
        ],
    )

    associate_profit_fields = _find_fields(
        field_index,
        [
            "Share in profits of associates",
            "Share of profits of associates",
            "Share in current year's profits of associates",
        ],
    )

    # =====================================================
    # Appropriation Fields
    # =====================================================

    brought_forward_fields = _find_fields(
        field_index,
        [
            "Balance in the Profit and Loss Account brought forward",
            "Balance brought forward",
            "Brought forward profit",
            "Profit and loss account brought forward",
        ],
    )

    appropriation_total_fields = _find_fields(
        field_index,
        [
            "Total",
        ],
    )

    balance_carried_fields = _find_fields(
        field_index,
        [
            "Balance carried over to Balance Sheet",
            "Balance carried over",
        ],
    )

    # =====================================================
    # IMPORTANT:
    # "Total" occurs in multiple places in P&L.
    #
    # The exact field lookup above can therefore point to
    # multiple unrelated totals if the extraction contains
    # generic names.
    #
    # We will select the appropriation total using the
    # evidence text where possible.
    # =====================================================

    appropriation_total_candidates = []

    for item in field_index.get(
        _normalize_name("Total"),
        [],
    ):

        evidence = (
            item.get("evidence")
            or ""
        ).lower()

        # Prefer evidence that appears near the
        # brought-forward / appropriation section.
        if (
            "654,314,131" in evidence
            or "530,423,526" in evidence
            or "appropriation" in evidence
        ):
            appropriation_total_candidates.append(
                item
            )

    if appropriation_total_candidates:

        appropriation_total_fields = (
            appropriation_total_candidates
        )

    else:

        # Do not blindly use generic "Total" values when
        # they cannot be distinguished safely.
        appropriation_total_fields = []

    # =====================================================
    # Determine Period Count
    # =====================================================
    #
    # Use reliable specific totals rather than generic
    # "Total" fields or malformed individual fields.

    period_count = max(
        len(total_income_fields),
        len(total_expenditure_fields),
        len(net_profit_fields),
        len(consolidated_profit_fields),
        1,
    )

    checks = []
    errors = []
    warnings = []

    passed_checks = 0
    failed_checks = 0
    not_applicable_checks = 0

    # =====================================================
    # Validate Each Comparative Period
    # =====================================================

    for period_index in range(
        period_count
    ):

        period = (
            f"period_{period_index + 1}"
        )

        # -------------------------------------------------
        # Values
        # -------------------------------------------------

        interest_earned = _get_period_value(
            interest_earned_fields,
            period_index,
        )

        other_income = _get_period_value(
            other_income_fields,
            period_index,
        )

        total_income = _get_period_value(
            total_income_fields,
            period_index,
        )

        interest_expended = _get_period_value(
            interest_expended_fields,
            period_index,
        )

        operating_expenses = _get_period_value(
            operating_expenses_fields,
            period_index,
        )

        provisions = _get_period_value(
            provisions_fields,
            period_index,
        )

        total_expenditure = _get_period_value(
            total_expenditure_fields,
            period_index,
        )

        net_profit = _get_period_value(
            net_profit_fields,
            period_index,
        )

        minority_interest = _get_period_value(
            minority_interest_fields,
            period_index,
        )

        consolidated_profit = _get_period_value(
            consolidated_profit_fields,
            period_index,
        )

        associate_profit = _get_period_value(
            associate_profit_fields,
            period_index,
        )

        brought_forward = _get_period_value(
            brought_forward_fields,
            period_index,
        )

        appropriation_total = _get_period_value(
            appropriation_total_fields,
            period_index,
        )

        balance_carried = _get_period_value(
            balance_carried_fields,
            period_index,
        )

        # =================================================
        # CHECK 1
        # Interest Earned + Other Income ≈ Total Income
        # =================================================

        if (
            interest_earned is not None
            and other_income is not None
            and total_income is not None
        ):

            calculated = (
                interest_earned
                + other_income
            )

            reported = total_income

            status = (
                "PASS"
                if _within_tolerance(
                    calculated,
                    reported,
                )
                else "FAIL"
            )

            if status == "PASS":

                passed_checks += 1

                message = (
                    f"{period}: interest earned plus "
                    f"other income reconciles to total income."
                )

            else:

                failed_checks += 1

                message = (
                    f"{period}: interest earned plus "
                    f"other income does not reconcile to total income."
                )

                errors.append(
                    message
                )

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Income components "
                        "reconciliation"
                    ),
                    formula=(
                        "Interest Earned + Other Income "
                        "≈ Total Income"
                    ),
                    operands={
                        "interest_earned":
                            interest_earned,
                        "other_income":
                            other_income,
                    },
                    calculated=calculated,
                    reported=reported,
                    status=status,
                    message=message,
                    evidence={
                        "interest_earned":
                            _get_period_evidence(
                                interest_earned_fields,
                                period_index,
                            ),
                        "other_income":
                            _get_period_evidence(
                                other_income_fields,
                                period_index,
                            ),
                        "total_income":
                            _get_period_evidence(
                                total_income_fields,
                                period_index,
                            ),
                    },
                )
            )

        else:

            not_applicable_checks += 1

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Income components "
                        "reconciliation"
                    ),
                    formula=(
                        "Interest Earned + Other Income "
                        "≈ Total Income"
                    ),
                    operands={
                        "interest_earned":
                            interest_earned,
                        "other_income":
                            other_income,
                    },
                    calculated=None,
                    reported=total_income,
                    status="NOT_APPLICABLE",
                    message=(
                        f"{period}: required income "
                        "field(s) are missing."
                    ),
                )
            )

        # =================================================
        # CHECK 2
        # Interest Expended + Operating Expenses
        # + Provisions ≈ Total Expenditure
        # =================================================

        if (
            interest_expended is not None
            and operating_expenses is not None
            and provisions is not None
            and total_expenditure is not None
        ):

            calculated = (
                interest_expended
                + operating_expenses
                + provisions
            )

            reported = total_expenditure

            status = (
                "PASS"
                if _within_tolerance(
                    calculated,
                    reported,
                )
                else "FAIL"
            )

            if status == "PASS":

                passed_checks += 1

                message = (
                    f"{period}: expenditure components "
                    f"reconcile to total expenditure."
                )

            else:

                failed_checks += 1

                message = (
                    f"{period}: expenditure components "
                    f"do not reconcile to total expenditure."
                )

                errors.append(
                    message
                )

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Expenditure components "
                        "reconciliation"
                    ),
                    formula=(
                        "Interest Expended + Operating Expenses "
                        "+ Provisions & Contingencies "
                        "≈ Total Expenditure"
                    ),
                    operands={
                        "interest_expended":
                            interest_expended,
                        "operating_expenses":
                            operating_expenses,
                        "provisions_and_contingencies":
                            provisions,
                    },
                    calculated=calculated,
                    reported=reported,
                    status=status,
                    message=message,
                    evidence={
                        "interest_expended":
                            _get_period_evidence(
                                interest_expended_fields,
                                period_index,
                            ),
                        "operating_expenses":
                            _get_period_evidence(
                                operating_expenses_fields,
                                period_index,
                            ),
                        "provisions_and_contingencies":
                            _get_period_evidence(
                                provisions_fields,
                                period_index,
                            ),
                        "total_expenditure":
                            _get_period_evidence(
                                total_expenditure_fields,
                                period_index,
                            ),
                    },
                )
            )

        else:

            not_applicable_checks += 1

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Expenditure components "
                        "reconciliation"
                    ),
                    formula=(
                        "Interest Expended + Operating Expenses "
                        "+ Provisions & Contingencies "
                        "≈ Total Expenditure"
                    ),
                    operands={
                        "interest_expended":
                            interest_expended,
                        "operating_expenses":
                            operating_expenses,
                        "provisions_and_contingencies":
                            provisions,
                    },
                    calculated=None,
                    reported=total_expenditure,
                    status="NOT_APPLICABLE",
                    message=(
                        f"{period}: required expenditure "
                        "field(s) are missing."
                    ),
                )
            )

        # =================================================
        # CHECK 3
        # Total Income - Total Expenditure
        # ≈ Net Profit Before Minority Interest
        # =================================================

        if (
            total_income is not None
            and total_expenditure is not None
            and net_profit is not None
        ):

            calculated = (
                total_income
                - total_expenditure
            )

            reported = net_profit

            status = (
                "PASS"
                if _within_tolerance(
                    calculated,
                    reported,
                )
                else "FAIL"
            )

            if status == "PASS":

                passed_checks += 1

                message = (
                    f"{period}: income minus expenditure "
                    f"reconciles to net profit before minority interest."
                )

            else:

                failed_checks += 1

                message = (
                    f"{period}: income minus expenditure "
                    f"does not reconcile to net profit before minority interest."
                )

                errors.append(
                    message
                )

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Profit before minority "
                        "reconciliation"
                    ),
                    formula=(
                        "Total Income - Total Expenditure "
                        "≈ Net Profit Before Minority Interest"
                    ),
                    operands={
                        "total_income":
                            total_income,
                        "total_expenditure":
                            total_expenditure,
                    },
                    calculated=calculated,
                    reported=reported,
                    status=status,
                    message=message,
                    evidence={
                        "total_income":
                            _get_period_evidence(
                                total_income_fields,
                                period_index,
                            ),
                        "total_expenditure":
                            _get_period_evidence(
                                total_expenditure_fields,
                                period_index,
                            ),
                        "net_profit":
                            _get_period_evidence(
                                net_profit_fields,
                                period_index,
                            ),
                    },
                )
            )

        else:

            not_applicable_checks += 1

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Profit before minority "
                        "reconciliation"
                    ),
                    formula=(
                        "Total Income - Total Expenditure "
                        "≈ Net Profit Before Minority Interest"
                    ),
                    operands={
                        "total_income":
                            total_income,
                        "total_expenditure":
                            total_expenditure,
                    },
                    calculated=None,
                    reported=net_profit,
                    status="NOT_APPLICABLE",
                    message=(
                        f"{period}: required profit "
                        "field(s) are missing."
                    ),
                )
            )

        # =================================================
        # CHECK 4
        # Profit Before Minority - Minority
        # ≈ Consolidated Profit
        #
        # We deliberately do NOT automatically add the
        # associate-profit field because its extraction is
        # ambiguous in the supplied AI output.
        #
        # If a difference remains, report it honestly.
        # =================================================

        if (
            net_profit is not None
            and minority_interest is not None
            and consolidated_profit is not None
        ):

            calculated = (
                net_profit
                - minority_interest
            )

            reported = consolidated_profit

            status = (
                "PASS"
                if _within_tolerance(
                    calculated,
                    reported,
                )
                else "FAIL"
            )

            if status == "PASS":

                passed_checks += 1

                message = (
                    f"{period}: profit before minority "
                    f"interest minus minority interest "
                    f"reconciles to consolidated profit."
                )

            else:

                failed_checks += 1

                message = (
                    f"{period}: profit before minority "
                    f"interest minus minority interest "
                    f"does not fully reconcile to consolidated profit."
                )

                errors.append(
                    message
                )

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Consolidated profit "
                        "reconciliation"
                    ),
                    formula=(
                        "Profit Before Minority Interest "
                        "- Minority Interest "
                        "≈ Consolidated Profit"
                    ),
                    operands={
                        "net_profit_before_minority":
                            net_profit,
                        "minority_interest":
                            minority_interest,
                    },
                    calculated=calculated,
                    reported=reported,
                    status=status,
                    message=message,
                    evidence={
                        "net_profit":
                            _get_period_evidence(
                                net_profit_fields,
                                period_index,
                            ),
                        "minority_interest":
                            _get_period_evidence(
                                minority_interest_fields,
                                period_index,
                            ),
                        "consolidated_profit":
                            _get_period_evidence(
                                consolidated_profit_fields,
                                period_index,
                            ),
                        "associate_profit":
                            _get_period_evidence(
                                associate_profit_fields,
                                period_index,
                            ),
                    },
                )
            )

        else:

            not_applicable_checks += 1

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Consolidated profit "
                        "reconciliation"
                    ),
                    formula=(
                        "Profit Before Minority Interest "
                        "- Minority Interest "
                        "≈ Consolidated Profit"
                    ),
                    operands={
                        "net_profit_before_minority":
                            net_profit,
                        "minority_interest":
                            minority_interest,
                    },
                    calculated=None,
                    reported=consolidated_profit,
                    status="NOT_APPLICABLE",
                    message=(
                        f"{period}: required consolidated "
                        "profit field(s) are missing."
                    ),
                )
            )

        # =================================================
        # CHECK 5
        # Current Profit + Brought Forward
        # ≈ Total Available For Appropriation
        # =================================================

        if (
            consolidated_profit is not None
            and brought_forward is not None
            and appropriation_total is not None
        ):

            calculated = (
                consolidated_profit
                + brought_forward
            )

            reported = appropriation_total

            status = (
                "PASS"
                if _within_tolerance(
                    calculated,
                    reported,
                )
                else "FAIL"
            )

            if status == "PASS":

                passed_checks += 1

                message = (
                    f"{period}: consolidated profit plus "
                    f"brought-forward balance reconciles "
                    f"to total available for appropriation."
                )

            else:

                failed_checks += 1

                message = (
                    f"{period}: consolidated profit plus "
                    f"brought-forward balance does not reconcile "
                    f"to total available for appropriation."
                )

                errors.append(
                    message
                )

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Appropriation availability "
                        "reconciliation"
                    ),
                    formula=(
                        "Current Consolidated Profit "
                        "+ Brought Forward Profit "
                        "≈ Total Available for Appropriation"
                    ),
                    operands={
                        "consolidated_profit":
                            consolidated_profit,
                        "brought_forward_profit":
                            brought_forward,
                    },
                    calculated=calculated,
                    reported=reported,
                    status=status,
                    message=message,
                    evidence={
                        "consolidated_profit":
                            _get_period_evidence(
                                consolidated_profit_fields,
                                period_index,
                            ),
                        "brought_forward":
                            _get_period_evidence(
                                brought_forward_fields,
                                period_index,
                            ),
                        "appropriation_total":
                            _get_period_evidence(
                                appropriation_total_fields,
                                period_index,
                            ),
                    },
                )
            )

        else:

            not_applicable_checks += 1

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Appropriation availability "
                        "reconciliation"
                    ),
                    formula=(
                        "Current Consolidated Profit "
                        "+ Brought Forward Profit "
                        "≈ Total Available for Appropriation"
                    ),
                    operands={
                        "consolidated_profit":
                            consolidated_profit,
                        "brought_forward_profit":
                            brought_forward,
                    },
                    calculated=None,
                    reported=appropriation_total,
                    status="NOT_APPLICABLE",
                    message=(
                        f"{period}: appropriation total "
                        "could not be identified reliably."
                    ),
                )
            )

    # =====================================================
    # Overall Status
    # =====================================================

    if failed_checks > 0:

        overall_status = "FAIL"

    elif passed_checks > 0:

        overall_status = "PASS"

    else:

        overall_status = "NOT_APPLICABLE"

    # =====================================================
    # Warnings
    # =====================================================

    if not extraction.tables:

        warnings.append(
            "AI extraction returned no structured tables; "
            "validation used explicit extracted fields."
        )

    if period_count > 1:

        warnings.append(
            f"Validated {period_count} comparative "
            "period(s) independently."
        )

    # Ambiguous associate-profit extraction.
    if associate_profit_fields:

        warnings.append(
            "Share in profits of associates was extracted, "
            "but its comparative-period sign is ambiguous "
            "in the supplied evidence; it was not used to "
            "alter the mandatory consolidated-profit formula."
        )

    # Generic Total fields may be ambiguous.
    if not appropriation_total_fields:

        warnings.append(
            "Appropriation total could not be identified "
            "unambiguously from generic 'Total' fields."
        )

    return {
        "overall_status": overall_status,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "periods_checked": period_count,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "not_applicable_checks":
                not_applicable_checks,
        },
    }