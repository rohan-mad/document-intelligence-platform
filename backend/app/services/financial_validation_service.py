import re
from typing import Optional


TOLERANCE = 0.01


# -------------------------------------------------
# Number parsing
# -------------------------------------------------

def parse_number(value) -> Optional[float]:
    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    if text in {"-", "—", "–", "null", "None"}:
        return None

    negative = False

    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]

    text = text.replace(",", "")
    text = text.replace("₹", "")
    text = text.replace("$", "")
    text = text.replace("€", "")
    text = text.replace("£", "")
    text = text.replace("%", "")

    match = re.search(r"-?\d+(?:\.\d+)?", text)

    if not match:
        return None

    number = float(match.group())

    if negative:
        number = -abs(number)

    return number


# -------------------------------------------------
# Description helpers
# -------------------------------------------------

def normalize_description(value: str) -> str:
    text = str(value or "").lower()

    text = text.replace("&", " and ")

    text = re.sub(r"[^a-z0-9]+", " ", text)

    return " ".join(text.split())


def find_line_item(
    line_items: list[dict],
    possible_names: list[str]
) -> Optional[dict]:

    normalized_targets = [
        normalize_description(name)
        for name in possible_names
    ]

    normalized_targets = [
        target
        for target in normalized_targets
        if target
    ]

    # First pass: exact matches across ALL rows
    for item in line_items:

        description = str(
            item.get("description") or ""
        ).strip()

        if not description:
            continue

        normalized_description = normalize_description(
            description
        )

        for target in normalized_targets:

            if normalized_description == target:
                return item

    # Second pass: cautious partial matching
    for item in line_items:

        description = str(
            item.get("description") or ""
        ).strip()

        if not description:
            continue

        normalized_description = normalize_description(
            description
        )

        for target in normalized_targets:

            if len(target) >= 12 and (
                target in normalized_description
                or normalized_description in target
            ):
                return item

    return None


def get_period_value(
    item: Optional[dict],
    period: Optional[str]
) -> Optional[float]:

    if not item:
        return None

    values = item.get("values") or []

    for entry in values:

        if period is None or entry.get("period") == period:
            return parse_number(entry.get("value"))

    return None


def get_periods(data: dict) -> list[str]:
    periods = data.get("periods") or []

    return [
        str(period)
        for period in periods
        if period
    ]


# -------------------------------------------------
# Validation check builder
# -------------------------------------------------

def make_check(
    formula: str,
    operands: dict,
    calculated: Optional[float],
    reported: Optional[float]
) -> dict:

    if calculated is None or reported is None:

        return {
            "formula": formula,
            "operands": operands,
            "calculated": calculated,
            "reported": reported,
            "variance": None,
            "status": "NOT_APPLICABLE"
        }

    variance = calculated - reported

    status = (
        "PASS"
        if abs(variance) <= TOLERANCE
        else "FAIL"
    )

    return {
        "formula": formula,
        "operands": operands,
        "calculated": round(calculated, 2),
        "reported": round(reported, 2),
        "variance": round(variance, 2),
        "status": status
    }


def summarize_validation(checks: list[dict]) -> dict:

    applicable = [
        check
        for check in checks
        if check["status"] != "NOT_APPLICABLE"
    ]

    if not applicable:

        overall_status = "NOT_APPLICABLE"

    elif any(
        check["status"] == "FAIL"
        for check in applicable
    ):

        overall_status = "FAIL"

    else:

        overall_status = "PASS"

    issues = [
        check
        for check in checks
        if check["status"] == "FAIL"
    ]

    return {
        "checks": checks,
        "overall_status": overall_status,
        "issues": issues
    }


# -------------------------------------------------
# Cash Flow Statement validation
# -------------------------------------------------

def validate_cash_flow(data: dict) -> dict:

    line_items = data.get("line_items") or []
    periods = get_periods(data)

    checks = []

    for period in periods:

        operating_item = find_line_item(
            line_items,
            [
                "Net cash from operating activities",
                "Net cash flow from operating activities",
                "Cash generated from operating activities",
                "Operating activities"
            ]
        )

        investing_item = find_line_item(
            line_items,
            [
                "Net cash used in investing activities",
                "Net cash from investing activities",
                "Cash used in investing activities",
                "Investing activities"
            ]
        )

        financing_item = find_line_item(
            line_items,
            [
                "Net cash used in financing activities",
                "Net cash from financing activities",
                "Cash used in financing activities",
                "Financing activities"
            ]
        )

        fx_item = find_line_item(
            line_items,
            [
                "Effect of exchange rate changes",
                "Effect of foreign exchange rate changes",
                "Exchange rate changes"
            ]
        )

        net_increase_item = find_line_item(
            line_items,
            [
                "Net increase in cash and cash equivalents",
                "Net increase in cash",
                "Increase in cash and cash equivalents"
            ]
        )

        acquisition_item = find_line_item(
            line_items,
            [
                "Cash and cash equivalents on amalgamation",
                "Cash acquired on amalgamation",
                "Cash acquired",
                "Cash on amalgamation"
            ]
        )

        operating = get_period_value(
            operating_item,
            period
        )

        investing = get_period_value(
            investing_item,
            period
        )

        financing = get_period_value(
            financing_item,
            period
        )

        fx = get_period_value(
            fx_item,
            period
        )

        net_increase = get_period_value(
            net_increase_item,
            period
        )

        acquisition = get_period_value(
            acquisition_item,
            period
        )

        if fx is None:
            fx = 0.0

        if acquisition is None:
            acquisition = 0.0

        calculated = None

        if (
            operating is not None
            and investing is not None
            and financing is not None
        ):

            calculated = (
                operating
                + investing
                + financing
                + fx
                + acquisition
            )

        checks.append(
            make_check(
                formula=(
                    "Operating + Investing + Financing "
                    "+ FX + Cash acquired = Net increase"
                ),
                operands={
                    "period": period,
                    "operating_activities": operating,
                    "investing_activities": investing,
                    "financing_activities": financing,
                    "fx_effect": fx,
                    "cash_acquired_on_amalgamation": acquisition
                },
                calculated=calculated,
                reported=net_increase
            )
        )

    return summarize_validation(checks)


# -------------------------------------------------
# Invoice validation
# -------------------------------------------------

def validate_invoice(data: dict) -> dict:

    line_items = data.get("line_items") or []
    fields = data.get("fields") or []

    checks = []

    # ---------------------------------------------
    # Line item quantity x unit price = line total
    # ---------------------------------------------

    for item in line_items:

        description = normalize_description(
            item.get("description")
        )

        values = item.get("values") or []

        if not values:
            continue

        # Generic line-item support:
        # if OCR/extraction produced values only,
        # leave exact arithmetic validation
        # to summary-level checks unless
        # explicit quantity/unit price fields exist.
        continue

    # ---------------------------------------------
    # Helpers for invoice fields
    # ---------------------------------------------

    def find_field(names: list[str]):

        targets = [
            normalize_description(name)
            for name in names
        ]

        for field in fields:

            field_name = normalize_description(
                field.get("name")
            )

            for target in targets:

                if field_name == target:
                    return parse_number(
                        field.get("value")
                    )

                if (
                    len(target) >= 8
                    and (
                        target in field_name
                        or field_name in target
                    )
                ):
                    return parse_number(
                        field.get("value")
                    )

        return None

    subtotal = find_field(
        [
            "subtotal",
            "sub total",
            "net amount"
        ]
    )

    tax = find_field(
        [
            "tax",
            "tax amount",
            "sales tax",
            "vat",
            "gst"
        ]
    )

    total = find_field(
        [
            "total",
            "invoice total",
            "grand total",
            "amount due"
        ]
    )

    cash_paid = find_field(
        [
            "cash paid",
            "amount paid",
            "paid"
        ]
    )

    change = find_field(
        [
            "change",
            "change due"
        ]
    )

    # subtotal + tax = total
    if (
        subtotal is not None
        and tax is not None
        and total is not None
    ):

        checks.append(
            make_check(
                formula="Subtotal + Tax = Total",
                operands={
                    "subtotal": subtotal,
                    "tax": tax
                },
                calculated=subtotal + tax,
                reported=total
            )
        )

    # cash paid - total = change
    if (
        cash_paid is not None
        and total is not None
        and change is not None
    ):

        checks.append(
            make_check(
                formula="Cash Paid - Total = Change",
                operands={
                    "cash_paid": cash_paid,
                    "total": total
                },
                calculated=cash_paid - total,
                reported=change
            )
        )

    return summarize_validation(checks)


# -------------------------------------------------
# Balance Sheet validation
# -------------------------------------------------


def validate_balance_sheet(data: dict) -> dict:

    line_items = data.get("line_items") or []
    periods = get_periods(data)

    checks = []

    for period in periods:

        capital_item = find_line_item(
            line_items,
            ["Capital"]
        )

        reserves_item = find_line_item(
            line_items,
            ["Reserves and surplus"]
        )

        minority_item = find_line_item(
            line_items,
            ["Minority interest"]
        )

        deposits_item = find_line_item(
            line_items,
            ["Deposits"]
        )

        borrowings_item = find_line_item(
            line_items,
            ["Borrowings"]
        )

        other_liabilities_item = find_line_item(
            line_items,
            ["Other liabilities and provisions"]
        )

        assets_item = find_line_item(
            line_items,
            ["Assets total"]
        )

        # The extracted document may label
        # the final assets row simply as "Total".
        if assets_item is None:

            totals = [
                item
                for item in line_items
                if normalize_description(
                    item.get("description")
                ) == "total"
            ]

            if len(totals) >= 2:
                assets_item = totals[1]

        capital = get_period_value(
            capital_item,
            period
        )

        reserves = get_period_value(
            reserves_item,
            period
        )

        minority = get_period_value(
            minority_item,
            period
        )

        deposits = get_period_value(
            deposits_item,
            period
        )

        borrowings = get_period_value(
            borrowings_item,
            period
        )

        other_liabilities = get_period_value(
            other_liabilities_item,
            period
        )

        assets = get_period_value(
            assets_item,
            period
        )

        calculated = None

        if all(
            value is not None
            for value in [
                capital,
                reserves,
                minority,
                deposits,
                borrowings,
                other_liabilities
            ]
        ):

            calculated = (
                capital
                + reserves
                + minority
                + deposits
                + borrowings
                + other_liabilities
            )

        checks.append(
            make_check(
                formula=(
                    "Capital + Reserves + Minority Interest "
                    "+ Deposits + Borrowings "
                    "+ Other Liabilities and Provisions = Assets"
                ),
                operands={
                    "period": period,
                    "capital": capital,
                    "reserves_and_surplus": reserves,
                    "minority_interest": minority,
                    "deposits": deposits,
                    "borrowings": borrowings,
                    "other_liabilities_and_provisions":
                        other_liabilities
                },
                calculated=calculated,
                reported=assets
            )
        )

    return summarize_validation(checks)


# -------------------------------------------------
# Profit & Loss validation
# -------------------------------------------------

def validate_profit_and_loss(data: dict) -> dict:

    line_items = data.get("line_items") or []
    periods = get_periods(data)

    checks = []

    for period in periods:

        interest_earned_item = find_line_item(
            line_items,
            [
                "interest earned",
                "interest income"
            ]
        )

        other_income_item = find_line_item(
            line_items,
            [
                "other income"
            ]
        )

        total_income_item = find_line_item(
            line_items,
            [
                "total income"
            ]
        )

        interest_expended_item = find_line_item(
            line_items,
            [
                "interest expended",
                "interest expense",
                "finance cost"
            ]
        )

        operating_expenses_item = find_line_item(
            line_items,
            [
                "operating expenses",
                "operating expenditure",
                "operating expense"
            ]
        )

        provisions_item = find_line_item(
            line_items,
            [
                "provisions",
                "provision"
            ]
        )

        total_expenditure_item = find_line_item(
            line_items,
            [
                "total expenditure",
                "total expenses",
                "total expense"
            ]
        )

        consolidated_profit_item = find_line_item(
            line_items,
            [
                "consolidated net profit before minority interest",
                "net profit before minority interest",
                "profit before minority interest"
            ]
        )

        minority_interest_item = find_line_item(
            line_items,
            [
                "minority interest"
            ]
        )

        group_profit_item = find_line_item(
            line_items,
            [
                "group net profit",
                "net profit attributable to group",
                "profit attributable to group"
            ]
        )

        interest_earned = get_period_value(
            interest_earned_item,
            period
        )

        other_income = get_period_value(
            other_income_item,
            period
        )

        total_income = get_period_value(
            total_income_item,
            period
        )

        interest_expended = get_period_value(
            interest_expended_item,
            period
        )

        operating_expenses = get_period_value(
            operating_expenses_item,
            period
        )

        provisions = get_period_value(
            provisions_item,
            period
        )

        total_expenditure = get_period_value(
            total_expenditure_item,
            period
        )

        consolidated_profit = get_period_value(
            consolidated_profit_item,
            period
        )

        minority_interest = get_period_value(
            minority_interest_item,
            period
        )

        group_profit = get_period_value(
            group_profit_item,
            period
        )

        # Total income
        income_calculated = None

        if (
            interest_earned is not None
            and other_income is not None
        ):

            income_calculated = (
                interest_earned
                + other_income
            )

        checks.append(
            make_check(
                formula="Interest Earned + Other Income = Total Income",
                operands={
                    "period": period,
                    "interest_earned": interest_earned,
                    "other_income": other_income
                },
                calculated=income_calculated,
                reported=total_income
            )
        )

        # Total expenditure
        expenditure_calculated = None

        if (
            interest_expended is not None
            and operating_expenses is not None
            and provisions is not None
        ):

            expenditure_calculated = (
                interest_expended
                + operating_expenses
                + provisions
            )

        checks.append(
            make_check(
                formula=(
                    "Interest Expended + Operating Expenses "
                    "+ Provisions = Total Expenditure"
                ),
                operands={
                    "period": period,
                    "interest_expended": interest_expended,
                    "operating_expenses": operating_expenses,
                    "provisions": provisions
                },
                calculated=expenditure_calculated,
                reported=total_expenditure
            )
        )

        # Consolidated profit
        profit_calculated = None

        if (
            total_income is not None
            and total_expenditure is not None
        ):

            profit_calculated = (
                total_income
                - total_expenditure
            )

        checks.append(
            make_check(
                formula=(
                    "Total Income - Total Expenditure "
                    "= Consolidated Net Profit Before Minority Interest"
                ),
                operands={
                    "period": period,
                    "total_income": total_income,
                    "total_expenditure": total_expenditure
                },
                calculated=profit_calculated,
                reported=consolidated_profit
            )
        )

        # Group profit
        group_profit_calculated = None

        if (
            consolidated_profit is not None
            and minority_interest is not None
        ):

            group_profit_calculated = (
                consolidated_profit
                - minority_interest
            )

        checks.append(
            make_check(
                formula=(
                    "Consolidated Profit Before Minority Interest "
                    "- Minority Interest = Group Net Profit"
                ),
                operands={
                    "period": period,
                    "consolidated_profit_before_minority_interest":
                        consolidated_profit,
                    "minority_interest": minority_interest
                },
                calculated=group_profit_calculated,
                reported=group_profit
            )
        )

    return summarize_validation(checks)


# -------------------------------------------------
# Generic financial validation dispatcher
# -------------------------------------------------

def validate_financial_document(
    data: dict,
    document_type: str
) -> dict:

    if document_type == "invoice":
        return validate_invoice(data)

    if document_type == "balance_sheet":
        return validate_balance_sheet(data)

    if document_type == "profit_and_loss":
        return validate_profit_and_loss(data)

    if document_type == "cash_flow_statement":
        return validate_cash_flow(data)

    return {
        "checks": [],
        "overall_status": "NOT_APPLICABLE",
        "issues": []
    }