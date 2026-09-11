from backend.app.schemas.extraction import (
    ExtractionResult,
)
from backend.app.services.cash_flow_validation_service import (
    validate_cash_flow,
)


# =========================================================
# Test Cash Flow Validator
# =========================================================

def main():
    extraction = ExtractionResult(
        document_type="cash_flow_statement",

        fields=[
            # 2018
            {
                "name": "Net cash from operating activities",
                "value": "272,242,758",
                "evidence": "Net cash from operating activities 272,242,758 249,663,120",
                "confidence": 1.0,
            },
            {
                "name": "Net cash used in investing activities",
                "value": "99,204",
                "evidence": "Net cash used in investing activities 99,204 100,768",
                "confidence": 1.0,
            },
            {
                "name": "Net cash (used in) / from financing activities",
                "value": "573,776,603",
                "evidence": "Net cash (used in) / from financing activities 573,776,603 (58,929,743)",
                "confidence": 1.0,
            },
            {
                "name": "Effect of exchange fluctuation on translation reserve",
                "value": "105,872",
                "evidence": "Effect of exchange fluctuation on translation reserve 105,872 (282,622)",
                "confidence": 1.0,
            },
            {
                "name": "Cash and cash equivalents on amalgamation",
                "value": "-",
                "evidence": "Cash and cash equivalents on amalgamation - 295,617",
                "confidence": 1.0,
            },
            {
                "name": "Net increase in cash and cash equivalents",
                "value": "737,504,366",
                "evidence": "Net increase in cash and cash equivalents 737,504,366 102,422,381",
                "confidence": 1.0,
            },
            {
                "name": "Cash and cash equivalents as at April 1st",
                "value": "493,111,196",
                "evidence": "Cash and cash equivalents as at April 1st 493,111,196 390,688,815",
                "confidence": 1.0,
            },
            {
                "name": "Cash and cash equivalents as at March 31st",
                "value": "1,230,615,562",
                "evidence": "Cash and cash equivalents as at March 31st 1,230,615,562 493,111,196",
                "confidence": 1.0,
            },

            # 2017
            {
                "name": "Net cash from operating activities",
                "value": "249,663,120",
                "evidence": "Net cash from operating activities 272,242,758 249,663,120",
                "confidence": 1.0,
            },
            {
                "name": "Net cash used in investing activities",
                "value": "100,768",
                "evidence": "Net cash used in investing activities 99,204 100,768",
                "confidence": 1.0,
            },
            {
                "name": "Net cash (used in) / from financing activities",
                "value": "(58,929,743)",
                "evidence": "Net cash (used in) / from financing activities 573,776,603 (58,929,743)",
                "confidence": 1.0,
            },
            {
                "name": "Effect of exchange fluctuation on translation reserve",
                "value": "(282,622)",
                "evidence": "Effect of exchange fluctuation on translation reserve 105,872 (282,622)",
                "confidence": 1.0,
            },
            {
                "name": "Cash and cash equivalents on amalgamation",
                "value": "295,617",
                "evidence": "Cash and cash equivalents on amalgamation - 295,617",
                "confidence": 1.0,
            },
            {
                "name": "Net increase in cash and cash equivalents",
                "value": "102,422,381",
                "evidence": "Net increase in cash and cash equivalents 737,504,366 102,422,381",
                "confidence": 1.0,
            },
            {
                "name": "Cash and cash equivalents as at April 1st",
                "value": "390,688,815",
                "evidence": "Cash and cash equivalents as at April 1st 493,111,196 390,688,815",
                "confidence": 1.0,
            },
            {
                "name": "Cash and cash equivalents as at March 31st",
                "value": "493,111,196",
                "evidence": "Cash and cash equivalents as at March 31st 1,230,615,562 493,111,196",
                "confidence": 1.0,
            },
        ],

        tables=[],
    )

    result = validate_cash_flow(
        extraction
    )

    print(
        "\n"
        "====================================\n"
        "CASH FLOW VALIDATION RESULT\n"
        "====================================\n"
    )

    print(
        f"Overall Status: "
        f"{result['overall_status']}\n"
    )

    print(
        f"Periods Checked: "
        f"{result['summary']['periods_checked']}\n"
    )

    print(
        f"Passed Checks: "
        f"{result['summary']['passed_checks']}\n"
    )

    print(
        f"Failed Checks: "
        f"{result['summary']['failed_checks']}\n"
    )

    print(
        f"Not Applicable Checks: "
        f"{result['summary']['not_applicable_checks']}\n"
    )

    print(
        "\nChecks:"
    )

    for check in result["checks"]:

        print(
            "\n------------------------------------"
        )

        print(
            f"Check: "
            f"{check['check']}"
        )

        print(
            f"Formula: "
            f"{check['formula']}"
        )

        print(
            f"Operands: "
            f"{check['operands']}"
        )

        print(
            f"Calculated: "
            f"{check['calculated']}"
        )

        print(
            f"Reported: "
            f"{check['reported']}"
        )

        print(
            f"Variance: "
            f"{check['variance']}"
        )

        print(
            f"Status: "
            f"{check['status']}"
        )

        print(
            f"Message: "
            f"{check['message']}"
        )

    print(
        "\nWarnings:"
    )

    for warning in result["warnings"]:
        print(
            f"- {warning}"
        )

    print(
        "\nErrors:"
    )

    for error in result["errors"]:
        print(
            f"- {error}"
        )


if __name__ == "__main__":
    main()