from datetime import date
from decimal import Decimal

import loans_sim.constants as C
from loans_sim.assets.savings_account.high_yield import HighYieldSavingsAccount


def test_average_monthly_yield():
    savings_account = HighYieldSavingsAccount(
        as_of_date=date(2020, 1, 1),
        vendor="test",
        apy=0.12,
    )

    assert savings_account.average_monthly_yield == 0.01
    assert savings_account.total_value == 0


def test_high_yield_savings_account_advanced_after_one_month_zero_stays_zero():
    savings_account = HighYieldSavingsAccount(
        as_of_date=date(2020, 1, 1),
        vendor="test",
        apy=0.12,
    )

    after_one_month = savings_account.after_one_month()

    assert after_one_month is not savings_account  # new instance
    assert after_one_month.balance == C.ZERO_DOLLARS_DECIMAL


def test_high_yield_savings_account_advanced_after_one_month_simple_one_percent():
    savings_account = HighYieldSavingsAccount(
        as_of_date=date(2020, 1, 1), vendor="test", apy=0.12, balance=Decimal("100.00")
    )

    after_one_month = savings_account.after_one_month()

    assert after_one_month is not savings_account  # new instance
    assert after_one_month.balance == Decimal("101.00")
