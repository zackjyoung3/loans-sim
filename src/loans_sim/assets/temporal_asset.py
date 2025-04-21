from abc import ABC, abstractmethod
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from typing import Self

from pydantic import BaseModel


class TemporalAsset(BaseModel, ABC):
    as_of_date: date

    @abstractmethod
    def _update_state_after_month_completed(self, new_date: date) -> Self:
        pass

    def after_one_month(self) -> Self:
        new_date = self.as_of_date + relativedelta(months=1)
        updated_instance = self._update_state_after_month_completed(new_date)
        updated_instance.as_of_date = new_date

        return updated_instance

    @property
    @abstractmethod
    def total_value(self) -> Decimal:
        pass
