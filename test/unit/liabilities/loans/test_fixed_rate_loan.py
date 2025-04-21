from decimal import Decimal

from loans_sim.liabilities.loans.fixed_rate_loan import FixedRateLoan


def test_interest_computed_correctly():
    loan = FixedRateLoan(
        vendor="TestBank",
        current_amount=Decimal(10500),
        principal=Decimal(10000),
        annual_interest_rate=0.06,
        monthly_payment=Decimal(500),
    )

    assert loan.interest == Decimal("500.00")


def test_monthly_interest_rate_computed_correctly():
    loan = FixedRateLoan(
        vendor="TestBank",
        current_amount=Decimal("10000.00"),
        principal=Decimal("10000.00"),
        annual_interest_rate=0.06,
        monthly_payment=Decimal("111.02"),
    )

    # 6% annually / 12 months = 0.5% monthly
    assert loan.monthly_interest_rate == 0.005


def test_is_paid_off_false():
    loan = FixedRateLoan(
        vendor="TestBank",
        current_amount=Decimal("200.00"),
        principal=Decimal("100.00"),
        annual_interest_rate=6.0,
        monthly_payment=Decimal("50.00"),
    )
    assert not loan.is_paid_off


def test_is_paid_off_true():
    loan = FixedRateLoan(
        vendor="TestBank",
        current_amount=Decimal("0.00"),
        principal=Decimal("0.00"),
        annual_interest_rate=6.0,
        monthly_payment=Decimal("50.00"),
    )
    assert loan.is_paid_off
