import re
from typing import Any

from backend.app.schemas.extraction import ExtractionResult


# =========================================================
# Number Parsing
# =========================================================

def _parse_number(value: Any) -> float | None:
    """
    Convert extracted financial values into numbers.

    Supports:
    - commas
    - currency symbols
    - parentheses for negative values
    - explicit minus signs
    - accounting dash as zero
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

    if text in {"-", "—", "–"}:
        return 0.0

    negative = False

    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()

    text = text.replace(",", "")
    text = text.replace("₹", "")
    text = text.replace("$", "")
    text = text.replace("€", "")
    text = text.replace("£", "")

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
# Field Name Normalization
# =========================================================

def _normalize_name(name: str) -> str:
    """
    Normalize field names for alias matching.
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
# Semantic Cash Flow Sign
# =========================================================

def _apply_cash_flow_semantic_sign(
    field_name: str,
    value: float | None,
) -> float | None:
    """
    Apply the economic sign implied by a cash-flow section label.

    Examples:
        "Net cash from operating activities"
            100 -> +100

        "Net cash used in investing activities"
            100 -> -100

        "Net cash (used in) / from financing activities"
            sign cannot safely be inferred from the label alone,
            so the extracted numeric sign is preserved.

    Explicit parentheses/minus signs are already handled by
    _parse_number().
    """

    if value is None:
        return None

    normalized = _normalize_name(
        field_name
    )

    # Financing labels containing both "used" and "from"
    # are ambiguous. Preserve the extracted numeric sign.
    if (
        "used in" in normalized
        and "from" in normalized
    ):
        return value

    # Pure "used in" section totals represent outflows.
    if "used in" in normalized:
        return -abs(value)

    # Pure "from" section totals represent inflows.
    if "from" in normalized:
        return abs(value)

    return value


# =========================================================
# Field Index
# =========================================================

def _build_field_index(
    extraction: ExtractionResult,
) -> dict[str, list[dict]]:
    """
    Group duplicate fields while preserving:

    - value
    - original field name
    - evidence
    """

    index: dict[str, list[dict]] = {}

    for field in extraction.fields:

        normalized_name = _normalize_name(
            field.name
        )

        index.setdefault(
            normalized_name,
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
# Alias Lookup
# =========================================================

def _find_field_values(
    field_index: dict[str, list[dict]],
    aliases: list[str],
) -> list[dict]:
    """
    Find fields using exact and fallback alias matching.
    """

    normalized_aliases = [
        _normalize_name(alias)
        for alias in aliases
    ]

    # Exact match
    for alias in normalized_aliases:

        if alias in field_index:
            return field_index[alias]

    # Contains match
    for field_name, values in field_index.items():

        for alias in normalized_aliases:

            if alias in field_name:
                return values

    return []


# =========================================================
# Value By Period
# =========================================================

def _value_for_period(
    field_values: list[dict],
    period_index: int,
    apply_semantic_sign: bool = False,
) -> float | None:
    """
    Retrieve a value for a comparative period.
    """

    if period_index >= len(field_values):
        return None

    item = field_values[
        period_index
    ]

    raw_value = item["value"]

    parsed = _parse_number(
        raw_value
    )

    if (
        parsed is not None
        and apply_semantic_sign
    ):
        parsed = _apply_cash_flow_semantic_sign(
            item["name"],
            parsed,
        )

    return parsed


# =========================================================
# Field Evidence
# =========================================================

def _evidence_for_period(
    field_values: list[dict],
    period_index: int,
) -> str | None:
    """
    Return source evidence for a specific extracted value.
    """

    if period_index >= len(field_values):
        return None

    return field_values[
        period_index
    ].get("evidence")


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
    Allow small absolute or relative rounding differences.
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
    Build standardized validation output.
    """

    variance = None

    if (
        calculated is not None
        and reported is not None
    ):
        variance = calculated - reported

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
# Cash Flow Validator
# =========================================================

def validate_cash_flow(
    extraction: ExtractionResult,
) -> dict:
    """
    Validate a Cash Flow Statement independently.

    Checks:

    1. Operating + Investing + Financing
       + applicable FX / other adjustments
       approximately equals Net Increase / Decrease.

    2. Opening Cash + Net Increase / Decrease
       approximately equals Closing Cash.

    Comparative periods are validated independently.
    """

    field_index = _build_field_index(
        extraction
    )

    # -----------------------------------------------------
    # Aliases
    # -----------------------------------------------------

    operating_aliases = [
        "Net cash from operating activities",
        "Net cash provided by operating activities",
        "Net cash generated from operating activities",
        "Net cash flow from operating activities",
    ]

    investing_aliases = [
        "Net cash used in investing activities",
        "Net cash from investing activities",
        "Net cash provided by investing activities",
        "Net cash flow from investing activities",
    ]

    financing_aliases = [
        "Net cash (used in) / from financing activities",
        "Net cash used in financing activities",
        "Net cash from financing activities",
        "Net cash provided by financing activities",
        "Net cash flow from financing activities",
    ]

    fx_aliases = [
        "Effect of exchange fluctuation on translation reserve",
        "Effect of exchange fluctuations",
        "Effect of exchange rate changes",
        "Foreign exchange adjustment",
        "FX adjustment",
        "Translation adjustment",
    ]

    other_aliases = [
        "Cash and cash equivalents on amalgamation",
        "Cash and cash equivalents on amalgamation [Refer Schedule 18(1)]",
        "Other cash adjustment",
        "Other adjustments to cash",
    ]

    net_change_aliases = [
        "Net increase in cash and cash equivalents",
        "Net decrease in cash and cash equivalents",
        "Net increase / decrease in cash and cash equivalents",
        "Net change in cash and cash equivalents",
        "Net change in cash",
    ]

    opening_aliases = [
        "Cash and cash equivalents as at April 1st",
        "Cash and cash equivalents as at April 1",
        "Opening cash and cash equivalents",
        "Opening cash",
    ]

    closing_aliases = [
        "Cash and cash equivalents as at March 31st",
        "Cash and cash equivalents as at March 31",
        "Closing cash and cash equivalents",
        "Closing cash",
    ]

    # -----------------------------------------------------
    # Retrieve fields
    # -----------------------------------------------------

    operating_fields = _find_field_values(
        field_index,
        operating_aliases,
    )

    investing_fields = _find_field_values(
        field_index,
        investing_aliases,
    )

    financing_fields = _find_field_values(
        field_index,
        financing_aliases,
    )

    fx_fields = _find_field_values(
        field_index,
        fx_aliases,
    )

    other_fields = _find_field_values(
        field_index,
        other_aliases,
    )

    net_change_fields = _find_field_values(
        field_index,
        net_change_aliases,
    )

    opening_fields = _find_field_values(
        field_index,
        opening_aliases,
    )

    closing_fields = _find_field_values(
        field_index,
        closing_aliases,
    )

    # -----------------------------------------------------
    # Number of comparative periods
    # -----------------------------------------------------

    period_count = max(
        len(operating_fields),
        len(investing_fields),
        len(financing_fields),
        len(net_change_fields),
        len(opening_fields),
        len(closing_fields),
        1,
    )

    period_labels = [
        f"period_{index + 1}"
        for index in range(period_count)
    ]

    checks = []
    errors = []
    warnings = []

    passed_checks = 0
    failed_checks = 0
    not_applicable_checks = 0

    # -----------------------------------------------------
    # Validate each period
    # -----------------------------------------------------

    for period_index in range(period_count):

        period = period_labels[
            period_index
        ]

        operating = _value_for_period(
            operating_fields,
            period_index,
            apply_semantic_sign=True,
        )

        investing = _value_for_period(
            investing_fields,
            period_index,
            apply_semantic_sign=True,
        )

        financing = _value_for_period(
            financing_fields,
            period_index,
            apply_semantic_sign=True,
        )

        fx = _value_for_period(
            fx_fields,
            period_index,
        )

        other = _value_for_period(
            other_fields,
            period_index,
        )

        net_change = _value_for_period(
            net_change_fields,
            period_index,
        )

        opening_cash = _value_for_period(
            opening_fields,
            period_index,
        )

        closing_cash = _value_for_period(
            closing_fields,
            period_index,
        )

        # -------------------------------------------------
        # CHECK 1
        # -------------------------------------------------

        flow_operands = {
            "operating_activities": operating,
            "investing_activities": investing,
            "financing_activities": financing,
            "fx_translation_adjustment": fx,
            "other_cash_adjustment": other,
        }

        required = [
            operating,
            investing,
            financing,
            net_change,
        ]

        if all(
            value is not None
            for value in required
        ):

            fx_value = (
                fx
                if fx is not None
                else 0.0
            )

            other_value = (
                other
                if other is not None
                else 0.0
            )

            calculated = (
                operating
                + investing
                + financing
                + fx_value
                + other_value
            )

            status = (
                "PASS"
                if _within_tolerance(
                    calculated,
                    net_change,
                )
                else "FAIL"
            )

            if status == "PASS":

                passed_checks += 1

                message = (
                    f"{period}: cash flow components "
                    f"reconcile to reported net change."
                )

            else:

                failed_checks += 1

                message = (
                    f"{period}: cash flow components "
                    f"do not reconcile to reported net change."
                )

                errors.append(
                    message
                )

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Cash flow components "
                        "reconciliation"
                    ),
                    formula=(
                        "Operating + Investing + "
                        "Financing + FX/Other "
                        "≈ Net Increase/Decrease"
                    ),
                    operands=flow_operands,
                    calculated=calculated,
                    reported=net_change,
                    status=status,
                    message=message,
                    evidence={
                        "operating": _evidence_for_period(
                            operating_fields,
                            period_index,
                        ),
                        "investing": _evidence_for_period(
                            investing_fields,
                            period_index,
                        ),
                        "financing": _evidence_for_period(
                            financing_fields,
                            period_index,
                        ),
                        "fx": _evidence_for_period(
                            fx_fields,
                            period_index,
                        ),
                        "other": _evidence_for_period(
                            other_fields,
                            period_index,
                        ),
                        "net_change": _evidence_for_period(
                            net_change_fields,
                            period_index,
                        ),
                    },
                )
            )

        else:

            not_applicable_checks += 1

            missing = []

            if operating is None:
                missing.append(
                    "operating activities"
                )

            if investing is None:
                missing.append(
                    "investing activities"
                )

            if financing is None:
                missing.append(
                    "financing activities"
                )

            if net_change is None:
                missing.append(
                    "net increase/decrease"
                )

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Cash flow components "
                        "reconciliation"
                    ),
                    formula=(
                        "Operating + Investing + "
                        "Financing + FX/Other "
                        "≈ Net Increase/Decrease"
                    ),
                    operands=flow_operands,
                    calculated=None,
                    reported=net_change,
                    status="NOT_APPLICABLE",
                    message=(
                        f"{period}: required value(s) "
                        f"missing: {', '.join(missing)}."
                    ),
                )
            )

        # -------------------------------------------------
        # CHECK 2
        # -------------------------------------------------

        cash_operands = {
            "opening_cash": opening_cash,
            "net_increase_decrease": net_change,
        }

        if (
            opening_cash is not None
            and net_change is not None
            and closing_cash is not None
        ):

            calculated_closing = (
                opening_cash
                + net_change
            )

            status = (
                "PASS"
                if _within_tolerance(
                    calculated_closing,
                    closing_cash,
                )
                else "FAIL"
            )

            if status == "PASS":

                passed_checks += 1

                message = (
                    f"{period}: opening cash plus "
                    f"net change reconciles to closing cash."
                )

            else:

                failed_checks += 1

                message = (
                    f"{period}: opening cash plus "
                    f"net change does not reconcile to closing cash."
                )

                errors.append(
                    message
                )

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Opening to closing cash "
                        "reconciliation"
                    ),
                    formula=(
                        "Opening Cash + "
                        "Net Increase/Decrease "
                        "≈ Closing Cash"
                    ),
                    operands=cash_operands,
                    calculated=calculated_closing,
                    reported=closing_cash,
                    status=status,
                    message=message,
                    evidence={
                        "opening_cash": _evidence_for_period(
                            opening_fields,
                            period_index,
                        ),
                        "net_change": _evidence_for_period(
                            net_change_fields,
                            period_index,
                        ),
                        "closing_cash": _evidence_for_period(
                            closing_fields,
                            period_index,
                        ),
                    },
                )
            )

        else:

            not_applicable_checks += 1

            missing = []

            if opening_cash is None:
                missing.append(
                    "opening cash"
                )

            if net_change is None:
                missing.append(
                    "net increase/decrease"
                )

            if closing_cash is None:
                missing.append(
                    "closing cash"
                )

            checks.append(
                _make_check(
                    period=period,
                    name=(
                        "Opening to closing cash "
                        "reconciliation"
                    ),
                    formula=(
                        "Opening Cash + "
                        "Net Increase/Decrease "
                        "≈ Closing Cash"
                    ),
                    operands=cash_operands,
                    calculated=None,
                    reported=closing_cash,
                    status="NOT_APPLICABLE",
                    message=(
                        f"{period}: required value(s) "
                        f"missing: {', '.join(missing)}."
                    ),
                )
            )

    # -----------------------------------------------------
    # Overall status
    # -----------------------------------------------------

    if failed_checks > 0:
        overall_status = "FAIL"

    elif passed_checks > 0:
        overall_status = "PASS"

    else:
        overall_status = "NOT_APPLICABLE"

    # -----------------------------------------------------
    # Warnings
    # -----------------------------------------------------

    if not extraction.tables:

        warnings.append(
            "AI extraction returned no structured tables; "
            "validation used extracted fields instead."
        )

    if period_count > 1:

        warnings.append(
            f"Validated {period_count} comparative "
            "period(s) independently."
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
            "not_applicable_checks": (
                not_applicable_checks
            ),
        },
    }