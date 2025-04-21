from decimal import Decimal

from pydantic import BaseModel, constr, computed_field

import loans_sim.constants as C
from loans_sim.custom_pydantic.annotations import DollarDecimal
from loans_sim.utils import get_monthly_interest_rate, round_dollar_to_nearest_cent


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
        return get_monthly_interest_rate(self.annual_interest_rate)

    @computed_field
    @property
    def is_paid_off(self) -> bool:
        return self.current_amount == C.ZERO_DOLLARS_DECIMAL
