from backend.app.schemas.extraction import (
    ExtractionResult,
)

from backend.app.services.profit_loss_validation_service import (
    validate_profit_loss,
)


def main():

    extraction = ExtractionResult(

        document_type="profit_and_loss",

        fields=[

            # =================================================
            # Period 1
            # =================================================

            {
                "name": "Interest earned",
                "value": "1,051,607,400",
                "evidence": "Interest earned 13 1,051,607,400 852,878,437",
                "confidence": 1.0,
            },
            {
                "name": "Other income",
                "value": "189,470,509",
                "evidence": "Other income 14 189,470,509 160,566,041",
                "confidence": 1.0,
            },
            {
                "name": "Total income",
                "value": "1,241,077,909",
                "evidence": "Total 1,241,077,909 1,013,444,478",
                "confidence": 1.0,
            },
            {
                "name": "Interest expended",
                "value": "537,126,876",
                "evidence": "Interest expended 15 537,126,876 423,814,803",
                "confidence": 1.0,
            },
            {
                "name": "Operating expenses",
                "value": "276,947,604",
                "evidence": "Operating expenses 16 276,947,604 239,272,220",
                "confidence": 1.0,
            },
            {
                "name": "Provisions and contingencies",
                "value": "202,547,300",
                "evidence": "Provisions and contingencies 202,547,300 164,749,045",
                "confidence": 1.0,
            },
            {
                "name": "Total expenditure",
                "value": "1,016,621,780",
                "evidence": "Total 1,016,621,780 827,836,068",
                "confidence": 1.0,
            },
            {
                "name": "Net profit for the year",
                "value": "224,456,129",
                "evidence": "Net profit for the year 224,456,129 185,608,410",
                "confidence": 1.0,
            },
            {
                "name": "Minority interest",
                "value": "1,131,820",
                "evidence": "Less: Minority interest 1,131,820 513,389",
                "confidence": 1.0,
            },
            {
                "name": "Share in profits of associates",
                "value": "-5,221",
                "evidence": "Add: Share in profits of associates - 5,221",
                "confidence": 1.0,
            },
            {
                "name": "Consolidated profit for the year",
                "value": "223,324,309",
                "evidence": "Consolidated profit for the year 223,324,309 185,100,242",
                "confidence": 1.0,
            },
            {
                "name": "Balance in the Profit and Loss Account brought forward",
                "value": "430,989,822",
                "evidence": "Balance in the Profit and Loss Account brought forward 430,989,822 345,323,284",
                "confidence": 1.0,
            },
            {
                "name": "Total",
                "value": "654,314,131",
                "evidence": "Total 654,314,131 530,423,526",
                "confidence": 1.0,
            },

            # =================================================
            # Period 2
            # =================================================

            {
                "name": "Interest earned",
                "value": "852,878,437",
                "evidence": "Interest earned 13 1,051,607,400 852,878,437",
                "confidence": 1.0,
            },
            {
                "name": "Other income",
                "value": "160,566,041",
                "evidence": "Other income 14 189,470,509 160,566,041",
                "confidence": 1.0,
            },
            {
                "name": "Total income",
                "value": "1,013,444,478",
                "evidence": "Total 1,241,077,909 1,013,444,478",
                "confidence": 1.0,
            },
            {
                "name": "Interest expended",
                "value": "423,814,803",
                "evidence": "Interest expended 15 537,126,876 423,814,803",
                "confidence": 1.0,
            },
            {
                "name": "Operating expenses",
                "value": "239,272,220",
                "evidence": "Operating expenses 16 276,947,604 239,272,220",
                "confidence": 1.0,
            },
            {
                "name": "Provisions and contingencies",
                "value": "164,749,045",
                "evidence": "Provisions and contingencies 202,547,300 164,749,045",
                "confidence": 1.0,
            },
            {
                "name": "Total expenditure",
                "value": "827,836,068",
                "evidence": "Total 1,016,621,780 827,836,068",
                "confidence": 1.0,
            },
            {
                "name": "Net profit for the year",
                "value": "185,608,410",
                "evidence": "Net profit for the year 224,456,129 185,608,410",
                "confidence": 1.0,
            },
            {
                "name": "Minority interest",
                "value": "513,389",
                "evidence": "Less: Minority interest 1,131,820 513,389",
                "confidence": 1.0,
            },
            {
                "name": "Share in profits of associates",
                "value": "5,221",
                "evidence": "Add: Share in profits of associates - 5,221",
                "confidence": 1.0,
            },
            {
                "name": "Consolidated profit for the year",
                "value": "185,100,242",
                "evidence": "Consolidated profit for the year 223,324,309 185,100,242",
                "confidence": 1.0,
            },
            {
                "name": "Balance in the Profit and Loss Account brought forward",
                "value": "345,323,284",
                "evidence": "Balance in the Profit and Loss Account brought forward 430,989,822 345,323,284",
                "confidence": 1.0,
            },
            {
                "name": "Total",
                "value": "530,423,526",
                "evidence": "Total 654,314,131 530,423,526",
                "confidence": 1.0,
            },
        ],

        tables=[],
    )

    result = validate_profit_loss(
        extraction
    )

    print(
        "\n"
        "====================================\n"
        "PROFIT & LOSS VALIDATION RESULT\n"
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
            f"Period: "
            f"{check['period']}"
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