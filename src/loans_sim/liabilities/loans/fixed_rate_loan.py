from collections import OrderedDict
from dataclasses import dataclass
from decimal import Decimal
from typing import Self

import polars as pl
from pydantic import BaseModel, constr, computed_field

import loans_sim.constants as C
from loans_sim.custom_pydantic.annotations import DollarDecimal
from loans_sim.utils import get_monthly_rate, round_dollar_to_nearest_cent


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
class PaymentRes:
    loan_status: "FixedRateLoan"  # forward ref to FixedRateLoan
    payment_info: PaymentInfo


def _make_payment_plan_info(loan: "FixedRateLoan", payment: PaymentInfo, month_no: int) -> dict:
    return {
        "Month": month_no,
        "Total Remaining": loan.current_amount,
        "Principal Remaining": loan.principal,
        "Interest Remaining": loan.interest,
        "Cum Total Paid": loan.lifetime_payments,
        "Monthly Principal Paid": payment.principal_paid,
        "Monthly Interest Paid": payment.interest_paid,
    }


class FixedRateLoan(BaseModel):
    """Simple interest assumed"""

    vendor: constr(min_length=1)
    current_amount: DollarDecimal
    principal: DollarDecimal
    annual_interest_rate: float
    monthly_payment: DollarDecimal
    lifetime_payments: DollarDecimal = round_dollar_to_nearest_cent(0)

    @computed_field
    @property
    def interest(self) -> Decimal:
        return self.current_amount - self.principal

    @computed_field
    @property
    def monthly_interest_rate(self) -> float:
        return get_monthly_rate(self.annual_interest_rate)

    @computed_field
    @property
    def is_paid_off(self) -> bool:
        return self.current_amount == C.ZERO_DOLLARS_DECIMAL

    def after_monthly_interest_accum(self) -> Self:
        """New instance of the loan after interest is accumulated for a month"""
        month_accum_interest = self.principal * Decimal(str(self.monthly_interest_rate))
        month_accum_interest = round_dollar_to_nearest_cent(month_accum_interest)
        current_amount_w_interest = self.current_amount + month_accum_interest

        return self.model_copy(update={"current_amount": current_amount_w_interest})

    def make_payment(self, payment: Decimal) -> PaymentRes:
        payment = round_dollar_to_nearest_cent(payment)
        possible_debit_for_principal = -(self.interest - payment)
        if possible_debit_for_principal > 0:
            interest_paid = self.interest
            principal_paid = min(possible_debit_for_principal, self.principal)
        else:
            interest_paid = payment
            principal_paid = C.ZERO_DOLLARS_DECIMAL
        payment_info = PaymentInfo(interest_paid=interest_paid, principal_paid=principal_paid)
        new_loan_state = self.model_copy(
            update={
                "current_amount": self.current_amount - payment_info.total_paid,
                "principal": self.principal - payment_info.principal_paid,
                "lifetime_payments": self.lifetime_payments + payment_info.total_paid,
            }
        )

        return PaymentRes(loan_status=new_loan_state, payment_info=payment_info)

    def make_monthly_payment(self) -> PaymentRes:
        """
        A monthly payment is a 2 step process in which
        1. The interest from the prev month is accumulated
        2. The loans monthly payment is applied to the loan with that accum interest
        """
        self_with_monthly_interest = self.after_monthly_interest_accum()
        return self_with_monthly_interest.make_payment(self.monthly_payment)

    def compute_payment_plan(self) -> pl.DataFrame:
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
        loan = self
        month = 1
        states = []

        while not loan.is_paid_off:
            payment_res = loan.make_monthly_payment()
            loan, payment_made = payment_res.loan_status, payment_res.payment_info
            states.append(_make_payment_plan_info(loan, payment_made, month))
            month += 1

        return pl.DataFrame(states, schema=PAYMENT_PLAN_SCHEMA)

    # use method rather than property for this as it is non-trivial computation
    def get_remaining_total_payment_req(self) -> Decimal:
        """
        Less efficient than amortized calculation obviously, but permits arbitrary start date calculations e.g.
        we resolve lifetime payment for a loan at any arbitrary state in terms of principal and interest rather than
        requiring that we just have initial amount (principal)
        """
        payment_plan = self.compute_payment_plan()
        if payment_plan.is_empty():
            return C.ZERO_DOLLARS_DECIMAL
        last_total = payment_plan.select(pl.last("Cum Total Paid")).item()
        return last_total - self.lifetime_payments
