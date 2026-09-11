from backend.app.schemas.extraction import (
    ExtractionResult,
)

from backend.app.services.balance_sheet_validation_service import (
    validate_balance_sheet,
)


def main():

    extraction = ExtractionResult(

        document_type="balance_sheet",

        fields=[

            # =================================================
            # Period 1
            # =================================================

            {
                "name": "Capital",
                "value": "5,190,181",
                "evidence": "Capital 1 5,190,181 5,125,091",
                "confidence": 0.0,
            },
            {
                "name": "Reserves and surplus",
                "value": "1,090,801,062",
                "evidence": "Reserves and surplus 2 1,090,801,062 912,814,397",
                "confidence": 0.0,
            },
            {
                "name": "Minority interest",
                "value": "3,563,322",
                "evidence": "Minority interest 2A 3,563,322 2,914,389",
                "confidence": 0.0,
            },

            # Deposits intentionally marked problematic
            # because the AI split the comparative values.
            {
                "name": "Deposits",
                "value": "7,883,751",
                "evidence": "Deposits 3 7,883,751 ,419 6,431 342,479",
                "confidence": 0.0,
            },
            {
                "name": "Deposits",
                "value": "419",
                "evidence": "Deposits 3 7,883,751 ,419 6,431 342,479",
                "confidence": 0.0,
            },
            {
                "name": "Deposits",
                "value": "6,431",
                "evidence": "Deposits 3 7,883,751 ,419 6,431 342,479",
                "confidence": 0.0,
            },
            {
                "name": "Deposits",
                "value": "342,479",
                "evidence": "Deposits 3 7,883,751 ,419 6,431 342,479",
                "confidence": 0.0,
            },

            {
                "name": "Borrowings",
                "value": "1,564,420,848",
                "evidence": "Borrowings 4 1,564,420,848 984,156,439",
                "confidence": 0.0,
            },
            {
                "name": "Other liabilities and provisions",
                "value": "484,134,863",
                "evidence": "Other liabilities and provisions 5 484,134,863 587,088,812",
                "confidence": 0.0,
            },
            {
                "name": "Total liabilities",
                "value": "11,031,861,695",
                "evidence": "Total 11,031,861,695 8,923,441 ,607",
                "confidence": 0.0,
            },

            {
                "name": "Cash and balances with Reserve Bank of India",
                "value": "1,046,882,074",
                "evidence": "Cash and balances with Reserve Bank of India 6 1,046,882,074 379,105,485",
                "confidence": 0.0,
            },
            {
                "name": "Balances with banks and money at call and short notice",
                "value": "183,733,488",
                "evidence": "Balances with banks and money at call and short notice 7 183,733,488 114,005,711",
                "confidence": 0.0,
            },
            {
                "name": "Investments",
                "value": "2,384,609,240",
                "evidence": "Investments 8 2,384,609,240 2,107,771,120",
                "confidence": 0.0,
            },
            {
                "name": "Advances",
                "value": "7,000,338,363",
                "evidence": "Advances 9 7,000,338,363 5,854,809,871",
                "confidence": 0.0,
            },
            {
                "name": "Fixed assets",
                "value": "38,105,583",
                "evidence": "Fixed assets 10 38,105,583 38,146,997",
                "confidence": 0.0,
            },
            {
                "name": "Other assets",
                "value": "378,192,947",
                "evidence": "Other assets 11 378,192,947 429,602,423",
                "confidence": 0.0,
            },
            {
                "name": "Total assets",
                "value": "11,031,861,695",
                "evidence": "Total 11,031,861,695 8,923,441 ,607",
                "confidence": 0.0,
            },

            # =================================================
            # Period 2
            # =================================================

            {
                "name": "Capital",
                "value": "5,125,091",
                "evidence": "Capital 1 5,190,181 5,125,091",
                "confidence": 0.0,
            },
            {
                "name": "Reserves and surplus",
                "value": "912,814,397",
                "evidence": "Reserves and surplus 2 1,090,801,062 912,814,397",
                "confidence": 0.0,
            },
            {
                "name": "Minority interest",
                "value": "2,914,389",
                "evidence": "Minority interest 2A 3,563,322 2,914,389",
                "confidence": 0.0,
            },

            {
                "name": "Borrowings",
                "value": "984,156,439",
                "evidence": "Borrowings 4 1,564,420,848 984,156,439",
                "confidence": 0.0,
            },
            {
                "name": "Other liabilities and provisions",
                "value": "587,088,812",
                "evidence": "Other liabilities and provisions 5 484,134,863 587,088,812",
                "confidence": 0.0,
            },
            {
                "name": "Total liabilities",
                "value": "8,923,441,607",
                "evidence": "Total 11,031,861,695 8,923,441 ,607",
                "confidence": 0.0,
            },

            {
                "name": "Cash and balances with Reserve Bank of India",
                "value": "379,105,485",
                "evidence": "Cash and balances with Reserve Bank of India 6 1,046,882,074 379,105,485",
                "confidence": 0.0,
            },
            {
                "name": "Balances with banks and money at call and short notice",
                "value": "114,005,711",
                "evidence": "Balances with banks and money at call and short notice 7 183,733,488 114,005,711",
                "confidence": 0.0,
            },
            {
                "name": "Investments",
                "value": "2,107,771,120",
                "evidence": "Investments 8 2,384,609,240 2,107,771,120",
                "confidence": 0.0,
            },
            {
                "name": "Advances",
                "value": "5,854,809,871",
                "evidence": "Advances 9 7,000,338,363 5,854,809,871",
                "confidence": 0.0,
            },
            {
                "name": "Fixed assets",
                "value": "38,146,997",
                "evidence": "Fixed assets 10 38,105,583 38,146,997",
                "confidence": 0.0,
            },
            {
                "name": "Other assets",
                "value": "429,602,423",
                "evidence": "Other assets 11 378,192,947 429,602,423",
                "confidence": 0.0,
            },
            {
                "name": "Total assets",
                "value": "8,923,441,607",
                "evidence": "Total 11,031,861,695 8,923,441 ,607",
                "confidence": 0.0,
            },
        ],

        tables=[],
    )

    result = validate_balance_sheet(
        extraction
    )

    print(
        "\n"
        "====================================\n"
        "BALANCE SHEET VALIDATION RESULT\n"
        "====================================\n"
    )

    print(
        f"Overall Status: "
        f"{result['overall_status']}"
    )

    print(
        f"\nPeriods Checked: "
        f"{result['summary']['periods_checked']}"
    )

    print(
        f"Passed Checks: "
        f"{result['summary']['passed_checks']}"
    )

    print(
        f"Failed Checks: "
        f"{result['summary']['failed_checks']}"
    )

    print(
        f"Not Applicable Checks: "
        f"{result['summary']['not_applicable_checks']}"
    )

    print(
        "\nChecks:"
    )

    for check in result["checks"]:

        print(
            "\n------------------------------------"
        )

        print(
            f"Period: {check['period']}"
        )

        print(
            f"Check: {check['check']}"
        )

        print(
            f"Formula: {check['formula']}"
        )

        print(
            f"Operands: {check['operands']}"
        )

        print(
            f"Calculated: {check['calculated']}"
        )

        print(
            f"Reported: {check['reported']}"
        )

        print(
            f"Variance: {check['variance']}"
        )

        print(
            f"Status: {check['status']}"
        )

        print(
            f"Message: {check['message']}"
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