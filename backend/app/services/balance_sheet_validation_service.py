import re
from typing import Any

from backend.app.schemas.extraction import ExtractionResult


# =========================================================
# Number Parsing
# =========================================================

def _parse_number(value: Any) -> float | None:
    """
    Convert an extracted financial value into a float.

    Supports:
    - commas
    - spaces inside numbers
    - currency symbols
    - parentheses for negative values
    - explicit negative values
    - accounting dash
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

    # Accounting dash means zero.
    if text in {"-", "—", "–"}:
        return 0.0

    negative = False

    # Parentheses mean negative.
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()

    # Remove separators and common currency symbols.
    text = text.replace(",", "")
    text = text.replace(" ", "")
    text = text.replace("₹", "")
    text = text.replace("$", "")
    text = text.replace("€", "")
    text = text.replace("£", "")

    # Keep only numeric characters.
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
    Normalize field names for reliable matching.
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
    Build an index while preserving duplicate occurrences.

    Comparative periods currently appear as repeated fields,
    so order is preserved.
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
    Find a field by exact match first,
    then by partial match.
    """

    normalized_aliases = [
        _normalize_name(alias)
        for alias in aliases
    ]

    # -----------------------------------------------
    # Exact matching
    # -----------------------------------------------

    for alias in normalized_aliases:

        if alias in field_index:
            return field_index[alias]

    # -----------------------------------------------
    # Partial matching
    # -----------------------------------------------

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
    """
    Get the extracted value for a comparative period.
    """

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
    """
    Get source evidence for a comparative period.
    """

    if period_index >= len(fields):
        return None

    return fields[
        period_index
    ].get("evidence")


# =========================================================
# Expected Period Count
# =========================================================

def _has_expected_period_count(
    fields: list[dict],
    period_count: int,
) -> bool:
    """
    A reliable comparative field should contain exactly
    one extracted value per period.

    More values than periods can indicate OCR or
    table-column segmentation problems.
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

    Relative tolerance:
        0.1%

    This allows small rounding differences.
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
    """
    Build a standardized validation check.
    """

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
# Component Sum
# =========================================================

def _sum_components(
    component_fields: list[tuple[str, list[dict]]],
    period_index: int,
    period_count: int,
) -> tuple[float | None, list[str]]:
    """
    Sum components only if every component has exactly one
    value for every comparative period.

    This prevents malformed fields from being interpreted
    as valid financial values.
    """

    total = 0.0
    invalid_components = []

    for name, fields in component_fields:

        # Component must contain exactly one value per period.
        if not _has_expected_period_count(
            fields,
            period_count,
        ):
            invalid_components.append(
                name
            )
            continue

        value = _get_period_value(
            fields,
            period_index,
        )

        if value is None:
            invalid_components.append(
                name
            )
            continue

        total += value

    if invalid_components:
        return None, invalid_components

    return total, []


# =========================================================
# Balance Sheet Validator
# =========================================================

def validate_balance_sheet(
    extraction: ExtractionResult,
) -> dict:
    """
    Validate a Balance Sheet.

    Checks:

    1. Total Capital & Liabilities ≈ Total Assets.
    2. Capital/Liability components ≈ Total Capital & Liabilities.
    3. Asset components ≈ Total Assets.

    Every comparative period is checked independently.

    Missing, ambiguous, duplicated, or malformed component
    fields result in NOT_APPLICABLE rather than an invented
    value or false failure.
    """

    field_index = _build_field_index(
        extraction
    )

    # =====================================================
    # Totals
    # =====================================================

    total_assets_fields = _find_fields(
        field_index,
        [
            "Total Assets",
            "Total Asset",
        ],
    )

    total_liabilities_fields = _find_fields(
        field_index,
        [
            "Total Liabilities",
            "Total Liability",
            "Total Capital & Liabilities",
            "Total Capital and Liabilities",
        ],
    )

    # =====================================================
    # Liability Components
    # =====================================================

    capital_fields = _find_fields(
        field_index,
        [
            "Capital",
        ],
    )

    reserves_fields = _find_fields(
        field_index,
        [
            "Reserves and surplus",
            "Reserves & surplus",
            "Reserves",
        ],
    )

    minority_fields = _find_fields(
        field_index,
        [
            "Minority interest",
            "Minority interests",
        ],
    )

    deposits_fields = _find_fields(
        field_index,
        [
            "Deposits",
        ],
    )

    borrowings_fields = _find_fields(
        field_index,
        [
            "Borrowings",
        ],
    )

    other_liabilities_fields = _find_fields(
        field_index,
        [
            "Other liabilities and provisions",
            "Other liabilities",
            "Liabilities and provisions",
        ],
    )

    # =====================================================
    # Asset Components
    # =====================================================

    cash_fields = _find_fields(
        field_index,
        [
            "Cash and balances with Reserve Bank of India",
            "Cash and balances with RBI",
            "Cash and bank balances",
        ],
    )

    bank_balances_fields = _find_fields(
        field_index,
        [
            "Balances with banks and money at call and short notice",
            "Balances with banks",
            "Money at call",
        ],
    )

    investments_fields = _find_fields(
        field_index,
        [
            "Investments",
        ],
    )

    advances_fields = _find_fields(
        field_index,
        [
            "Advances",
        ],
    )

    fixed_assets_fields = _find_fields(
        field_index,
        [
            "Fixed assets",
            "Fixed asset",
        ],
    )

    other_assets_fields = _find_fields(
        field_index,
        [
            "Other assets",
        ],
    )

    # =====================================================
    # Determine Comparative Period Count
    # =====================================================
    #
    # IMPORTANT:
    # Do NOT use individual fields such as Deposits because
    # malformed OCR can create extra values.
    #
    # Reliable statement totals determine the number of periods.

    period_count = max(
        len(total_assets_fields),
        len(total_liabilities_fields),
        1,
    )

    # =====================================================
    # Result Containers
    # =====================================================

    checks = []
    errors = []
    warnings = []

    passed_checks = 0
    failed_checks = 0
    not_applicable_checks = 0

    # =====================================================
    # Validate Each Period
    # =====================================================

    for period_index in range(
        period_count
    ):

        period = (
            f"period_{period_index + 1}"
        )

        total_assets = _get_period_value(
            total_assets_fields,
            period_index,
        )

        total_liabilities = _get_period_value(
            total_liabilities_fields,
            period_index,
        )

        # =================================================
        # CHECK 1
        # Total Capital & Liabilities ≈ Total Assets
        # =================================================

        if (
            total_liabilities is not None
            and total_assets is not None
        ):

            calculated = (
                total_liabilities
            )

            reported = (
                total_assets
            )

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
                    f"{period}: total capital and "
                    f"liabilities reconcile to total assets."
                )

            else:

                failed_checks += 1

                message = (
                    f"{period}: total capital and "
                    f"liabilities do not reconcile to total assets."
                )

                errors.append(
                    message
                )

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Total capital and liabilities "
                        "vs total assets"
                    ),
                    formula=(
                        "Total Capital & Liabilities "
                        "≈ Total Assets"
                    ),
                    operands={
                        "total_capital_liabilities":
                            total_liabilities,
                        "total_assets":
                            total_assets,
                    },
                    calculated=calculated,
                    reported=reported,
                    status=status,
                    message=message,
                    evidence={
                        "total_capital_liabilities":
                            _get_period_evidence(
                                total_liabilities_fields,
                                period_index,
                            ),
                        "total_assets":
                            _get_period_evidence(
                                total_assets_fields,
                                period_index,
                            ),
                    },
                )
            )

        else:

            not_applicable_checks += 1

            missing = []

            if total_liabilities is None:
                missing.append(
                    "total capital & liabilities"
                )

            if total_assets is None:
                missing.append(
                    "total assets"
                )

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Total capital and liabilities "
                        "vs total assets"
                    ),
                    formula=(
                        "Total Capital & Liabilities "
                        "≈ Total Assets"
                    ),
                    operands={
                        "total_capital_liabilities":
                            total_liabilities,
                        "total_assets":
                            total_assets,
                    },
                    calculated=None,
                    reported=total_assets,
                    status="NOT_APPLICABLE",
                    message=(
                        f"{period}: required field(s) "
                        f"missing: {', '.join(missing)}."
                    ),
                )
            )

        # =================================================
        # CHECK 2
        # Liability Components
        # =================================================

        liability_components = [
            (
                "capital",
                capital_fields,
            ),
            (
                "reserves_and_surplus",
                reserves_fields,
            ),
            (
                "minority_interest",
                minority_fields,
            ),
            (
                "deposits",
                deposits_fields,
            ),
            (
                "borrowings",
                borrowings_fields,
            ),
            (
                "other_liabilities_and_provisions",
                other_liabilities_fields,
            ),
        ]

        liability_sum, invalid_liabilities = (
            _sum_components(
                liability_components,
                period_index,
                period_count,
            )
        )

        liability_components_are_usable = (
            liability_sum is not None
            and total_liabilities is not None
        )

        if liability_components_are_usable:

            calculated = (
                liability_sum
            )

            reported = (
                total_liabilities
            )

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
                    f"{period}: capital and liability "
                    f"components reconcile."
                )

            else:

                failed_checks += 1

                message = (
                    f"{period}: capital and liability "
                    f"components do not reconcile."
                )

                errors.append(
                    message
                )

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Capital and liability "
                        "components reconciliation"
                    ),
                    formula=(
                        "Capital + Reserves + Minority "
                        "Interest + Deposits + Borrowings "
                        "+ Other Liabilities "
                        "≈ Total Capital & Liabilities"
                    ),
                    operands={
                        "capital":
                            _get_period_value(
                                capital_fields,
                                period_index,
                            ),
                        "reserves_and_surplus":
                            _get_period_value(
                                reserves_fields,
                                period_index,
                            ),
                        "minority_interest":
                            _get_period_value(
                                minority_fields,
                                period_index,
                            ),
                        "deposits":
                            _get_period_value(
                                deposits_fields,
                                period_index,
                            ),
                        "borrowings":
                            _get_period_value(
                                borrowings_fields,
                                period_index,
                            ),
                        "other_liabilities_and_provisions":
                            _get_period_value(
                                other_liabilities_fields,
                                period_index,
                            ),
                    },
                    calculated=calculated,
                    reported=reported,
                    status=status,
                    message=message,
                    evidence={
                        "capital":
                            _get_period_evidence(
                                capital_fields,
                                period_index,
                            ),
                        "reserves_and_surplus":
                            _get_period_evidence(
                                reserves_fields,
                                period_index,
                            ),
                        "minority_interest":
                            _get_period_evidence(
                                minority_fields,
                                period_index,
                            ),
                        "deposits":
                            _get_period_evidence(
                                deposits_fields,
                                period_index,
                            ),
                        "borrowings":
                            _get_period_evidence(
                                borrowings_fields,
                                period_index,
                            ),
                        "other_liabilities_and_provisions":
                            _get_period_evidence(
                                other_liabilities_fields,
                                period_index,
                            ),
                    },
                )
            )

        else:

            not_applicable_checks += 1

            reason = (
                ", ".join(
                    invalid_liabilities
                )
                if invalid_liabilities
                else "total capital & liabilities is missing"
            )

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Capital and liability "
                        "components reconciliation"
                    ),
                    formula=(
                        "Capital + Reserves + Minority "
                        "Interest + Deposits + Borrowings "
                        "+ Other Liabilities "
                        "≈ Total Capital & Liabilities"
                    ),
                    operands={},
                    calculated=None,
                    reported=total_liabilities,
                    status="NOT_APPLICABLE",
                    message=(
                        f"{period}: liability component "
                        f"validation cannot be completed; "
                        f"unusable component data: {reason}."
                    ),
                )
            )

        # =================================================
        # CHECK 3
        # Asset Components
        # =================================================

        asset_components = [
            (
                "cash_and_balances_with_rbi",
                cash_fields,
            ),
            (
                "balances_with_banks_and_money_at_call",
                bank_balances_fields,
            ),
            (
                "investments",
                investments_fields,
            ),
            (
                "advances",
                advances_fields,
            ),
            (
                "fixed_assets",
                fixed_assets_fields,
            ),
            (
                "other_assets",
                other_assets_fields,
            ),
        ]

        asset_sum, invalid_assets = (
            _sum_components(
                asset_components,
                period_index,
                period_count,
            )
        )

        asset_components_are_usable = (
            asset_sum is not None
            and total_assets is not None
        )

        if asset_components_are_usable:

            calculated = (
                asset_sum
            )

            reported = (
                total_assets
            )

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
                    f"{period}: asset components "
                    f"reconcile to total assets."
                )

            else:

                failed_checks += 1

                message = (
                    f"{period}: asset components "
                    f"do not reconcile to total assets."
                )

                errors.append(
                    message
                )

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Asset components "
                        "reconciliation"
                    ),
                    formula=(
                        "Cash + Bank Balances + "
                        "Investments + Advances + "
                        "Fixed Assets + Other Assets "
                        "≈ Total Assets"
                    ),
                    operands={
                        "cash_and_balances_with_rbi":
                            _get_period_value(
                                cash_fields,
                                period_index,
                            ),
                        "balances_with_banks_and_money_at_call":
                            _get_period_value(
                                bank_balances_fields,
                                period_index,
                            ),
                        "investments":
                            _get_period_value(
                                investments_fields,
                                period_index,
                            ),
                        "advances":
                            _get_period_value(
                                advances_fields,
                                period_index,
                            ),
                        "fixed_assets":
                            _get_period_value(
                                fixed_assets_fields,
                                period_index,
                            ),
                        "other_assets":
                            _get_period_value(
                                other_assets_fields,
                                period_index,
                            ),
                    },
                    calculated=calculated,
                    reported=reported,
                    status=status,
                    message=message,
                    evidence={
                        "cash_and_balances_with_rbi":
                            _get_period_evidence(
                                cash_fields,
                                period_index,
                            ),
                        "balances_with_banks_and_money_at_call":
                            _get_period_evidence(
                                bank_balances_fields,
                                period_index,
                            ),
                        "investments":
                            _get_period_evidence(
                                investments_fields,
                                period_index,
                            ),
                        "advances":
                            _get_period_evidence(
                                advances_fields,
                                period_index,
                            ),
                        "fixed_assets":
                            _get_period_evidence(
                                fixed_assets_fields,
                                period_index,
                            ),
                        "other_assets":
                            _get_period_evidence(
                                other_assets_fields,
                                period_index,
                            ),
                    },
                )
            )

        else:

            not_applicable_checks += 1

            reason = (
                ", ".join(
                    invalid_assets
                )
                if invalid_assets
                else "total assets is missing"
            )

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Asset components "
                        "reconciliation"
                    ),
                    formula=(
                        "Cash + Bank Balances + "
                        "Investments + Advances + "
                        "Fixed Assets + Other Assets "
                        "≈ Total Assets"
                    ),
                    operands={},
                    calculated=None,
                    reported=total_assets,
                    status="NOT_APPLICABLE",
                    message=(
                        f"{period}: asset component "
                        f"validation cannot be completed; "
                        f"unusable component data: {reason}."
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

    # Deposits is the known malformed field in the
    # currently tested document.
    if len(deposits_fields) != period_count:

        warnings.append(
            "Deposits contains an unexpected number of "
            "extracted values for the detected comparative "
            "periods; possible OCR/table-column "
            "segmentation issue."
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