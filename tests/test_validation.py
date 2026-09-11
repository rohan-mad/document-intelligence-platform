from backend.app.services.financial_validation_service import (
    validate_financial_document,
)


def make_item(description, values):
    return {
        "description": description,
        "values": [
            {
                "period": period,
                "value": str(value),
            }
            for period, value in values.items()
        ],
    }


def test_invoice_validation_pass():

    data = {
        "periods": ["2026"],
        "fields": [
            {"name": "Subtotal", "value": "1000"},
            {"name": "Tax", "value": "180"},
            {"name": "Total", "value": "1180"},
        ],
        "line_items": [],
    }

    result = validate_financial_document(
        data,
        "invoice"
    )

    assert result["overall_status"] == "PASS"


def test_balance_sheet_validation_pass():

    data = {
        "periods": ["2026"],
        "fields": [],
        "line_items": [
            make_item(
                "Capital",
                {"2026": 100}
            ),
            make_item(
                "Reserves and surplus",
                {"2026": 300}
            ),
            make_item(
                "Minority interest",
                {"2026": 50}
            ),
            make_item(
                "Deposits",
                {"2026": 700}
            ),
            make_item(
                "Borrowings",
                {"2026": 200}
            ),
            make_item(
                "Other liabilities and provisions",
                {"2026": 150}
            ),
            make_item(
                "Total",
                {"2026": 1500}
            ),
            make_item(
                "Total",
                {"2026": 1500}
            ),
        ],
    }

    result = validate_financial_document(
        data,
        "balance_sheet"
    )

    assert result["overall_status"] == "PASS"


def test_profit_and_loss_validation_pass():

    data = {
        "periods": ["2026"],
        "fields": [],
        "line_items": [
            make_item(
                "Interest Earned",
                {"2026": 1000}
            ),
            make_item(
                "Other Income",
                {"2026": 200}
            ),
            make_item(
                "Total Income",
                {"2026": 1200}
            ),
            make_item(
                "Interest Expended",
                {"2026": 400}
            ),
            make_item(
                "Operating Expenses",
                {"2026": 500}
            ),
            make_item(
                "Provisions",
                {"2026": 100}
            ),
            make_item(
                "Total Expenditure",
                {"2026": 1000}
            ),
            make_item(
                "Consolidated Net Profit Before Minority Interest",
                {"2026": 200}
            ),
            make_item(
                "Minority Interest",
                {"2026": 50}
            ),
            make_item(
                "Group Net Profit",
                {"2026": 150}
            ),
        ],
    }

    result = validate_financial_document(
        data,
        "profit_and_loss"
    )

    assert result["overall_status"] == "PASS"


def test_cash_flow_validation_pass():

    data = {
        "periods": ["2026"],
        "fields": [],
        "line_items": [
            make_item(
                "Net cash from operating activities",
                {"2026": 1000}
            ),
            make_item(
                "Net cash used in investing activities",
                {"2026": -200}
            ),
            make_item(
                "Net cash used in financing activities",
                {"2026": -300}
            ),
            make_item(
                "Effect of exchange rate changes",
                {"2026": 0}
            ),
            make_item(
                "Net increase in cash and cash equivalents",
                {"2026": 500}
            ),
        ],
    }

    result = validate_financial_document(
        data,
        "cash_flow_statement"
    )

    assert result["overall_status"] == "PASS"


def test_validation_failure():

    data = {
        "periods": ["2026"],
        "fields": [
            {"name": "Subtotal", "value": "1000"},
            {"name": "Tax", "value": "180"},
            {"name": "Total", "value": "1300"},
        ],
        "line_items": [],
    }

    result = validate_financial_document(
        data,
        "invoice"
    )

    assert result["overall_status"] == "FAIL"