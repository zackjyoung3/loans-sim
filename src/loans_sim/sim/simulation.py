from dataclasses import dataclass, field
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal

import plotly.graph_objects as go

from loans_sim.assets.savings_account.high_yield import HighYieldSavingsAccount
from loans_sim.assets.temporal_asset import TemporalAsset
from loans_sim.liabilities.loans.fixed_rate_loan import FixedRateLoan
from loans_sim.liabilities.loans.mitigation import simulate_savings_from_additional_payment


CAPITAL_AVAILABLE = Decimal("8_000")

sample_loan = FixedRateLoan(
    vendor="test_vendor",
    current_amount=Decimal("20_000.00"),
    principal=Decimal("18_000.00"),
    annual_interest_rate=0.08,
    monthly_payment=Decimal("600.00"),
)
loan_mitigation_info = simulate_savings_from_additional_payment(sample_loan, CAPITAL_AVAILABLE)

savings_account_if_capital_allocated = HighYieldSavingsAccount(
    as_of_date=date.today().replace(day=1),
    vendor="test_vendor",
    apy=0.035,
    balance=CAPITAL_AVAILABLE,
)


@dataclass(frozen=True)
class AccumTimeSeries:
    label: str
    time_points: list[date]
    value_points: list[Decimal]


@dataclass
class TimeSeriesAccumulator:
    time_points: list[date] = field(default_factory=list)
    value_points: list[Decimal] = field(default_factory=list)

    def __post_init__(self) -> None:
        if len(self.time_points) != len(self.value_points):
            raise ValueError("The length of time points and value points do not match")

    def _is_valid_next_time_point(self, time_point: date) -> bool:
        if not self.time_points:
            return True
        # right now assume we always have one month progressions
        return self.time_points[-1] + relativedelta(months=1) == time_point

    def add_point(self, time_point: date, value_point: Decimal) -> None:
        if not self._is_valid_next_time_point(time_point):
            # always have -1 bc we have a laste time point to check for validity here
            raise ValueError(
                f"Next time point {time_point} is not valid. Must be exactly one month after {self.time_points[-1]}"
            )
        self.time_points.append(time_point)
        self.value_points.append(value_point)

    def collect(self, label: str) -> AccumTimeSeries:
        return AccumTimeSeries(label, self.time_points, self.value_points)


def make_temporal_asset_time_series(asset: TemporalAsset, num_months: int = 12, label: str = None) -> AccumTimeSeries:
    label = label or str(asset)
    ts_accumulator = TimeSeriesAccumulator()
    original_val = asset.total_value

    # the first point is start value
    for _ in range(num_months + 1):
        ts_accumulator.add_point(asset.as_of_date, asset.total_value - original_val)
        asset = asset.after_one_month()
    return ts_accumulator.collect(label=label)


def make_const_ts_for_time_points(time_points: list[date], const_val: Decimal, label: str) -> AccumTimeSeries:
    return AccumTimeSeries(
        label=label,
        time_points=time_points,
        value_points=[const_val for _ in range(len(time_points))],
    )


savings_account_sim = make_temporal_asset_time_series(savings_account_if_capital_allocated, num_months=180)
loan_fixed_amount_saved = make_const_ts_for_time_points(
    savings_account_sim.time_points, const_val=loan_mitigation_info.lifetime_amount_saved, label="Loan Savings"
)


fig = go.Figure()
for accum_time_series in (savings_account_sim, loan_fixed_amount_saved):
    fig.add_trace(
        go.Scatter(
            x=accum_time_series.time_points,
            y=accum_time_series.value_points,
            mode="lines",
            name=accum_time_series.label,
        )
    )

fig.update_layout(title="Simulation Comparisons", xaxis_title="Month", yaxis_title="Total Earned/Saved")
fig.show()
