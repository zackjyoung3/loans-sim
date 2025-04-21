from collections import OrderedDict
from dataclasses import dataclass
from decimal import Decimal

import polars as pl
from pydantic import BaseModel, computed_field

from loans_sim import constants as C
from loans_sim.custom_pydantic.annotations import DollarDecimal
from loans_sim.liabilities.loans.fixed_rate_loan import FixedRateLoan
from loans_sim.utils import round_dollar_to_nearest_cent


PAYMENT_PLAN_SCHEMA = OrderedDict(
    [
        ("Month", pl.Int64),
        ("Total Remaining", pl.Decimal(scale=2)),
        ("Principal Remaining", pl.Decimal(scale=2)),
        ("Interest Remaining", pl.Decimal(scale=2)),
        ("Cum Total Paid", pl.Decimal(scale=2)),
        ("Monthly Principal Paid", pl.Decimal(scale=2)),
        ("Monthly Interest Paid", pl.Decimal(scale=2)),
    ]
)


class PaymentInfo(BaseModel):
    interest_paid: DollarDecimal
    principal_paid: DollarDecimal

    @computed_field
    @property
    def total_paid(self) -> Decimal:
        return self.interest_paid + self.principal_paid


@dataclass(frozen=True)
class MonthlyPaymentRes:
    loan_status: FixedRateLoan
    payment_info: PaymentInfo


def make_monthly_payment(loan: FixedRateLoan) -> MonthlyPaymentRes:
    month_accum_interest = loan.principal * Decimal(str(loan.monthly_interest_rate))
    month_accum_interest = round_dollar_to_nearest_cent(month_accum_interest)
    current_amount_w_interest = loan.current_amount + month_accum_interest

    total_interest = loan.interest + month_accum_interest
    possible_debit_for_principal = -(total_interest - loan.monthly_payment)
    if possible_debit_for_principal > 0:
        interest_paid = total_interest
        principal_paid = min(possible_debit_for_principal, loan.principal)
    else:
        interest_paid = loan.monthly_payment
        principal_paid = C.ZERO_DOLLARS_DECIMAL
    payment_info = PaymentInfo(interest_paid=interest_paid, principal_paid=principal_paid)
    new_loan_state = loan.model_copy(
        update={
            "current_amount": current_amount_w_interest - payment_info.total_paid,
            "principal": loan.principal - payment_info.principal_paid,
            "lifetime_payments": loan.lifetime_payments + payment_info.total_paid,
        }
    )

    return MonthlyPaymentRes(loan_status=new_loan_state, payment_info=payment_info)


def _make_payment_plan_info(loan: FixedRateLoan, payment: PaymentInfo, month_no: int) -> dict:
    return {
        "Month": month_no,
        "Total Remaining": loan.current_amount,
        "Principal Remaining": loan.principal,
        "Interest Remaining": loan.interest,
        "Cum Total Paid": loan.lifetime_payments,
        "Monthly Principal Paid": payment.principal_paid,
        "Monthly Interest Paid": payment.interest_paid,
    }


def make_payment_plan(loan: FixedRateLoan) -> pl.DataFrame:
    """
    Generate a polars DF with all information for the Payment plan of the form

    Note that this strictly adheres to the monthly payment plan that has been provided
    I have experimented with online tools that generate amortized payment plans and there will be very slight deviation
    (generally few cents on $10,000 basis) that result from the payment plans generated having some months where they
    state the payment as being a certain amount, but then have monthly payment exceed this payment by a cent.
    This implementation adheres absolute fidelity to the stated monthly payment plan.
    :param loan: the state of the loans that is to be paid off
    :return: a DataFrame with monthly payment plan information of the form
    ┌───────┬───────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
    │ Month ┆ Total         ┆ Principal    ┆ Interest     ┆ Cum Total    ┆ Monthly      ┆ Monthly      │
    │       ┆ Remaining     ┆ Remaining    ┆ Remaining    ┆ Paid         ┆ Principal    ┆ Interest     │
    │  ---  ┆ ---           ┆ ---          ┆ ---          ┆ ---          ┆ Paid         ┆ Paid         │
    ╞═══════╪═══════════════╪══════════════╪══════════════╪══════════════╪══════════════╪══════════════╡
    """
    month = 1
    states = []

    while not loan.is_paid_off:
        payment_res = make_monthly_payment(loan)
        loan, payment_made = payment_res.loan_status, payment_res.payment_info
        states.append(_make_payment_plan_info(loan, payment_made, month))
        month += 1

    return pl.DataFrame(states, schema=PAYMENT_PLAN_SCHEMA)


def get_total_payment_req(loan: FixedRateLoan) -> Decimal:
    """
    Less efficient than amortized calculation obviously, but permits arbitrary start date calculations e.g.
    we resolve lifetime payment for a loan at any arbitrary state in terms of principal and interest rather than
    requiring that we just have initial amount (principal)
    """
    payment_plan = make_payment_plan(loan)
    if payment_plan.is_empty():
        return C.ZERO_DOLLARS_DECIMAL
    return payment_plan.select(pl.last("Cum Total Paid")).item()
