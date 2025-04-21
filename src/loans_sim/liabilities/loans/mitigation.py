from decimal import Decimal

from loans_sim.liabilities.loans.fixed_rate_loan import FixedRateLoan
from loans_sim.liabilities.mitigation_action import LiabilityMitigationAction
from loans_sim.utils import round_dollar_to_nearest_cent

MAKE_ADDITIONAL_PAYMENT_ACTION_STR = "Make additional loan payment"


def simulate_savings_from_additional_payment(loan: FixedRateLoan, payment: Decimal) -> LiabilityMitigationAction:
    """For simplicity, assumes that extra payment made at beginning of month to avoid considering interest accum"""
    payment = round_dollar_to_nearest_cent(payment)

    no_action_total_payment = loan.get_remaining_total_payment_req()
    loan_after_payment = loan.make_payment(payment)
    payment_req_after_additional_payment = loan_after_payment.loan_status.get_remaining_total_payment_req()
    total_payment_with_additional_payment = payment_req_after_additional_payment + payment
    amount_saved = no_action_total_payment - total_payment_with_additional_payment

    return LiabilityMitigationAction(action=MAKE_ADDITIONAL_PAYMENT_ACTION_STR, lifetime_amount_saved=amount_saved)
