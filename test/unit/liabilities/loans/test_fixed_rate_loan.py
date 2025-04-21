# TODO: come back and refactor tests
#   I initially had more procedural approach to making monthly payments, but wanted to encapsulate
#   all logic for performing operations on the loan in a class for a more OOP approach
#   should come back and make explicit make_payment tests (being tested implicitly via make_monthly_payment
#   which would have all cases)
import copy
from decimal import Decimal

import polars as pl
import polars.testing as plt
import pytest

import loans_sim.constants as C
from loans_sim.liabilities.loans.fixed_rate_loan import FixedRateLoan, PAYMENT_PLAN_SCHEMA


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


# ensure total_paid updated correctly for from scratch + running total cases
@pytest.mark.parametrize("total_paid", [0, 200], ids=["first_payment", "subsequent_payment"])
def test_after_monthly_payment_payoff_less_than_accum_interest_plus_current_amount(total_paid: int):
    loan_in_state_to_be_paid_off_in_a_month = FixedRateLoan(
        vendor="TestBank",
        current_amount=Decimal("130.00"),
        principal=Decimal("100.00"),
        annual_interest_rate=0.12,
        monthly_payment=Decimal("150.00"),
        lifetime_payments=total_paid,
    )
    expected_paid = Decimal("131.00")  # 130 balance + (1% monthly * 100 principal)
    original = copy.deepcopy(loan_in_state_to_be_paid_off_in_a_month)

    after_payment_res = loan_in_state_to_be_paid_off_in_a_month.make_monthly_payment()
    after_payment = after_payment_res.loan_status
    payment_info = after_payment_res.payment_info

    assert loan_in_state_to_be_paid_off_in_a_month == original  # no side effects
    assert after_payment is not original  # new copy returned

    assert after_payment.current_amount == C.ZERO_DOLLARS_DECIMAL
    assert after_payment.principal == C.ZERO_DOLLARS_DECIMAL
    assert after_payment.lifetime_payments == Decimal(str(total_paid + expected_paid))
    assert after_payment.is_paid_off is True

    assert payment_info.interest_paid == 31
    assert payment_info.principal_paid == 100


# ensure total_paid updated correctly for from scratch + running total cases
@pytest.mark.parametrize("total_paid", [0, 200], ids=["first_payment", "subsequent_payment"])
def test_after_monthly_payment_only_interest_can_be_paid_off(total_paid: int):
    loan_only_interest_can_be_paid = FixedRateLoan(
        vendor="TestBank",
        current_amount=Decimal("130.00"),
        principal=Decimal("100.00"),
        annual_interest_rate=0.12,
        monthly_payment=Decimal("30.99"),
        lifetime_payments=total_paid,
    )
    expected_principal = loan_only_interest_can_be_paid.principal
    expected_paid = Decimal("30.99")  # full monthly payment expected
    expected_interest = Decimal("0.01")
    expected_total = expected_principal + expected_interest
    original = copy.deepcopy(loan_only_interest_can_be_paid)

    after_payment_res = loan_only_interest_can_be_paid.make_monthly_payment()
    after_payment = after_payment_res.loan_status
    payment_info = after_payment_res.payment_info

    assert loan_only_interest_can_be_paid == original  # no side effects
    assert after_payment is not original  # new copy returned

    assert after_payment.current_amount == expected_total
    assert after_payment.principal == expected_principal
    assert after_payment.interest == expected_interest
    assert after_payment.lifetime_payments == Decimal(str(total_paid + expected_paid))
    assert after_payment.is_paid_off is False

    assert payment_info.interest_paid == expected_paid
    assert payment_info.principal_paid == Decimal("0")


# ensure total_paid updated correctly for from scratch + running total cases
@pytest.mark.parametrize("total_paid", [0, 200], ids=["first_payment", "subsequent_payment"])
def test_after_monthly_payment_only_interest_can_be_paid_off_boundary(total_paid: int):
    loan_only_interest_can_be_paid = FixedRateLoan(
        vendor="TestBank",
        current_amount=Decimal("130.00"),
        principal=Decimal("100.00"),
        annual_interest_rate=0.12,
        monthly_payment=Decimal("31"),
        lifetime_payments=total_paid,
    )
    expected_principal = loan_only_interest_can_be_paid.principal
    expected_paid = Decimal("31")  # full monthly payment expected
    expected_interest = C.ZERO_DOLLARS_DECIMAL
    expected_total = expected_principal + expected_interest
    original = copy.deepcopy(loan_only_interest_can_be_paid)

    after_payment_res = loan_only_interest_can_be_paid.make_monthly_payment()
    after_payment = after_payment_res.loan_status
    payment_info = after_payment_res.payment_info

    assert loan_only_interest_can_be_paid == original  # no side effects
    assert after_payment is not original  # new copy returned

    assert after_payment.current_amount == expected_total
    assert after_payment.principal == expected_principal
    assert after_payment.interest == expected_interest
    assert after_payment.lifetime_payments == Decimal(str(total_paid + expected_paid))
    assert after_payment.is_paid_off is False

    assert payment_info.interest_paid == expected_paid
    assert payment_info.principal_paid == Decimal("0")


# ensure total_paid updated correctly for from scratch + running total cases
@pytest.mark.parametrize("total_paid", [0, 200], ids=["first_payment", "subsequent_payment"])
def test_after_monthly_payment_principal_can_be_paid_off(total_paid: int):
    loan_principal_can_be_paid_after_interest_paid = FixedRateLoan(
        vendor="TestBank",
        current_amount=Decimal("130.00"),
        principal=Decimal("100.00"),
        annual_interest_rate=0.12,
        monthly_payment=Decimal("50"),
        lifetime_payments=total_paid,
    )
    # 31 in interest paid off => 19 left over for principal
    expected_principal = loan_principal_can_be_paid_after_interest_paid.principal - Decimal("19.00")
    expected_paid = Decimal("50")  # full monthly payment expected
    expected_interest = C.ZERO_DOLLARS_DECIMAL
    expected_total = expected_principal + expected_interest
    original = copy.deepcopy(loan_principal_can_be_paid_after_interest_paid)

    after_payment_res = loan_principal_can_be_paid_after_interest_paid.make_monthly_payment()
    after_payment = after_payment_res.loan_status
    payment_info = after_payment_res.payment_info

    assert loan_principal_can_be_paid_after_interest_paid == original  # no side effects
    assert after_payment is not original  # new copy returned

    assert after_payment.current_amount == expected_total
    assert after_payment.principal == expected_principal
    assert after_payment.interest == expected_interest
    assert after_payment.lifetime_payments == Decimal(str(total_paid + expected_paid))
    assert after_payment.is_paid_off is False

    assert payment_info.interest_paid == Decimal("31")
    assert payment_info.principal_paid == Decimal("19")


def test_compute_payment_plan_loan_already_paid_off_empty():
    loan_in_state_to_be_paid_off_in_a_month = FixedRateLoan(
        vendor="TestBank",
        current_amount=Decimal("0.00"),
        principal=Decimal("0.00"),
        annual_interest_rate=0.12,
        monthly_payment=Decimal("150.00"),
    )

    payment_plan = loan_in_state_to_be_paid_off_in_a_month.compute_payment_plan()

    assert payment_plan.is_empty()
    assert payment_plan.schema == PAYMENT_PLAN_SCHEMA


def test_compute_payment_plan_one_month_payoff():
    loan_in_state_to_be_paid_off_in_a_month = FixedRateLoan(
        vendor="TestBank",
        current_amount=Decimal("130.00"),
        principal=Decimal("100.00"),
        annual_interest_rate=0.12,
        monthly_payment=Decimal("150.00"),
    )
    expected_single_month_info = {
        "Month": 1,
        "Total Remaining": Decimal("0.00"),
        "Principal Remaining": Decimal("0.00"),
        "Interest Remaining": Decimal("0.00"),
        "Cum Total Paid": Decimal("131.00"),
        "Monthly Principal Paid": Decimal("100.00"),
        "Monthly Interest Paid": Decimal("31.00"),
    }
    expected_df = pl.DataFrame(expected_single_month_info, schema=PAYMENT_PLAN_SCHEMA)
    payment_plan = loan_in_state_to_be_paid_off_in_a_month.compute_payment_plan()

    assert payment_plan.height == 1  # single payment req
    assert payment_plan.schema == PAYMENT_PLAN_SCHEMA
    plt.assert_frame_equal(payment_plan, expected_df)


def test_get_total_payment_req_no_payoff_case():
    loan_in_state_to_be_paid_off_in_a_month = FixedRateLoan(
        vendor="TestBank",
        current_amount=Decimal("0.00"),
        principal=Decimal("0.00"),
        annual_interest_rate=0.12,
        monthly_payment=Decimal("150.00"),
    )

    assert loan_in_state_to_be_paid_off_in_a_month.get_total_payment_req() == C.ZERO_DOLLARS_DECIMAL


def test_get_total_payment_req_one_month_payoff():
    loan_in_state_to_be_paid_off_in_a_month = FixedRateLoan(
        vendor="TestBank",
        current_amount=Decimal("130.00"),
        principal=Decimal("100.00"),
        annual_interest_rate=0.12,
        monthly_payment=Decimal("150.00"),
    )
    # 130 existing amount + 1 for interest accumulated in that month

    assert loan_in_state_to_be_paid_off_in_a_month.get_total_payment_req() == Decimal("131.00")


def test_get_total_payment_req_n_month_payoff():
    loan_in_state_to_be_paid_off_in_n_months = FixedRateLoan(
        vendor="TestBank",
        current_amount=Decimal("130.00"),
        principal=Decimal("100.00"),
        annual_interest_rate=0.12,
        monthly_payment=Decimal("50.00"),
    )
    # 50 first month off 131 => 81 remaining (50 paid)
    # 81 => .81 interest => 31.81 remaining (50 paid)
    # 31.81 => .32 interest => no remaining (32.13 paid)
    # 50 + 50 + 32.13 = 132.13 total

    assert loan_in_state_to_be_paid_off_in_n_months.get_total_payment_req() == Decimal("132.13")
