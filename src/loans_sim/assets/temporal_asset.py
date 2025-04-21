from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Self

from pydantic import BaseModel


class TemporalAsset(BaseModel, ABC):
    as_of_date: date

    @abstractmethod
    def after_one_month(self) -> Self:
        pass

    @property
    @abstractmethod
    def total_value(self) -> Decimal:
        pass
