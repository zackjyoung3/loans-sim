from decimal import Decimal, ROUND_HALF_UP

import polars as pl

import loans_sim.constants as C


def round_dollar_to_nearest_cent(val: int | float | str | Decimal) -> Decimal:
    if not isinstance(val, Decimal):
        try:
            val = Decimal(str(val)) if not isinstance(val, str) else Decimal(val)
        except Exception as e:
            raise ValueError(f"Converting to Decimal for dollar to nearest cent failed for val: {val}") from e
    return val.quantize(Decimal(C.DOLLAR_DECIMAL_QUANTIZE_VAL), rounding=ROUND_HALF_UP)


def get_monthly_rate(annual_rate: float) -> float:
    """
    Compute monthly rate given annual rate
    :param annual_rate: An annual rate where the float represents a percentage.
    e.g. pass 0.06 for 6%, 0.045 for 4.5%, etc.
    :return: the monthly rate
    """
    return annual_rate / C.MONTHS_IN_YEAR


def print_full_df(df: pl.DataFrame) -> None:
    with pl.Config() as cfg:
        cfg.set_tbl_cols(10_000)
        cfg.set_tbl_rows(10_000)

        print(df)
