from datetime import date
from decimal import Decimal
from typing import Self

from pydantic import computed_field, constr

from loans_sim.assets.temporal_asset import TemporalAsset
import loans_sim.constants as C
from loans_sim.custom_pydantic.annotations import DollarDecimal
from loans_sim.utils import get_monthly_rate, round_dollar_to_nearest_cent


class HighYieldSavingsAccount(TemporalAsset):
    as_of_date: date
    vendor: constr(min_length=1)
    apy: float
    balance: DollarDecimal = C.ZERO_DOLLARS_DECIMAL

    @computed_field
    @property
    def average_monthly_yield(self) -> float:
        return get_monthly_rate(self.apy)

    def _update_state_after_month_completed(self, new_date: date) -> Self:
        new_balance = self.balance + round_dollar_to_nearest_cent(
            self.balance * Decimal(str(self.average_monthly_yield))
        )
        return self.model_copy(update={"balance": new_balance})

    @property
    def total_value(self) -> Decimal:
        return self.balance
