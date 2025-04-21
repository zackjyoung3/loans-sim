from pydantic import BaseModel

from loans_sim.custom_pydantic.annotations import DollarDecimal


class LiabilityMitigationAction(BaseModel):
    action: str
    lifetime_amount_saved: DollarDecimal
