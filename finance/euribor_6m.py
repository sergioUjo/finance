import asyncio

import QuantLib as ql

from finance.fixings import apply_fixings
from finance.utils import get_swap_rate, get_ql_quotes_periods


async def curve():
    calendar = ql.TARGET()
    deposit_rate = ql.Euribor6M()
    data, historical_fixings = await asyncio.gather(
        get_swap_rate("EURIBOR", "6M"),
        apply_fixings("6M", calendar, deposit_rate, "EURIBOR"),
    )
    rate = historical_fixings
    helpers = []

    helpers.append(
        ql.DepositRateHelper(
            ql.QuoteHandle(ql.SimpleQuote(rate / 100)),
            ql.Period(6,ql.Months),
            2,
            calendar,
            ql.Following,
            False,
            ql.Actual360(),
        )
    )
    # Create helpers for each tenor
    for ql_quote_handle, ql_period in get_ql_quotes_periods(data):
        helper = ql.SwapRateHelper(
            ql_quote_handle,
            ql_period,
            calendar,
            ql.Annual,
            ql.Unadjusted,
            ql.Thirty360(ql.Thirty360.BondBasis),
            deposit_rate,
            ql.QuoteHandle(),
            ql.Period(0, ql.Days),
        )

        helpers.append(helper)
    curve = ql.PiecewiseLogCubicDiscount(
        0, calendar, helpers, ql.Actual365Fixed()
    )
    curve.enableExtrapolation()
    return curve
