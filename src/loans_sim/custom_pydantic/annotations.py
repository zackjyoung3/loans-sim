from typing import Annotated

from pydantic import BeforeValidator, condecimal

import loans_sim.constants as C
from loans_sim.utils import round_dollar_to_nearest_cent

DollarDecimal = Annotated[
    condecimal(decimal_places=C.DOLLAR_DECIMAL_SCALE),
    BeforeValidator(round_dollar_to_nearest_cent),
]
