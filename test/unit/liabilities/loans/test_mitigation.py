# TODO: come back and beef up tests
from decimal import Decimal

from loans_sim.liabilities.loans.fixed_rate_loan import FixedRateLoan
from loans_sim.liabilities.loans.mitigation import (
    MAKE_ADDITIONAL_PAYMENT_ACTION_STR,
    simulate_savings_from_additional_payment,
)


def test_simulate_savings_from_additional_pay_all_vs_over_n_months():
    loan_full_amount = Decimal("130.00")
    loan_in_state_to_be_paid_off_in_n_months = FixedRateLoan(
        vendor="TestBank",
        current_amount=loan_full_amount,
        principal=Decimal("100.00"),
        annual_interest_rate=0.12,
        monthly_payment=Decimal("50.00"),
    )
    # 50 first month off 131 => 81 remaining (50 paid)
    # 81 => .81 interest => 31.81 remaining (50 paid)
    # 31.81 => .32 interest => no remaining (32.13 paid)
    # 50 + 50 + 32.13 = 132.13 total => 2.13 saved

    savings_info = simulate_savings_from_additional_payment(loan_in_state_to_be_paid_off_in_n_months, loan_full_amount)

    assert savings_info.action == MAKE_ADDITIONAL_PAYMENT_ACTION_STR
    assert savings_info.lifetime_amount_saved == Decimal("2.13")


def test_simulate_savings_from_additional_pay_partial_vs_over_n_months():
    loan_in_state_to_be_paid_off_in_n_months = FixedRateLoan(
        vendor="TestBank",
        current_amount=Decimal("130.00"),
        principal=Decimal("100.00"),
        annual_interest_rate=0.12,
        monthly_payment=Decimal("50.00"),
    )
    # 132.13 total from above
    # only .81 + .32 = 1.13 interest paid from above starting at second payment
    # => savings = 2.13 - 1.13 = 1.00
    payment_to_get_down_to_81 = Decimal("49.00")

    savings_info = simulate_savings_from_additional_payment(
        loan_in_state_to_be_paid_off_in_n_months, payment_to_get_down_to_81
    )

    assert savings_info.action == MAKE_ADDITIONAL_PAYMENT_ACTION_STR
    assert savings_info.lifetime_amount_saved == Decimal("1.00")
