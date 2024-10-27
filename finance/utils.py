from datetime import datetime

import QuantLib as ql
from matplotlib import pyplot as plt
from pypika import Query, Table

from finance.db import query_db


async def get_swap_rate(index_name, index):

    real_time = Table("taxa_fixa_swap_rates_real_time")

    query = (
        Query.from_(real_time)
        .select("*")
        .where(real_time.index_name == index_name)
    )
    if index is not None:
        query = query.where(real_time.index == index)
    swaps = await query_db(str(query))
    return swaps

def curve_values(curve,index):
    ##create a max date that is 5 years from now
    max_date = curve.referenceDate() + ql.Period("5Y")
    schedule = ql.MakeSchedule(
        curve.referenceDate(), max_date, ql.Period("1M")
    )

    # Extract discount factors at each date in the schedule
    times = []
    rates = []

    for date in schedule:
        #iso string datetime
        py_datetime = datetime(date.year(), date.month(), date.dayOfMonth())
        times.append(py_datetime.timestamp())
        rates.append(
            curve.forwardRate(
                date,
                ql.TARGET().advance(date, ql.Period(index)),
                ql.Actual360(),
                ql.Simple,
            ).rate()
        )
    return times, rates

def plot_curve(curve):
    """Function to plot the discount factors using a schedule."""

    # Create a schedule based on the curve's reference and max date, with 3M intervals
    schedule = ql.MakeSchedule(
        curve.referenceDate(), curve.maxDate(), ql.Period("1M")
    )

    # Extract discount factors at each date in the schedule
    times = []
    discount_factors = []

    for date in schedule:
        t = ql.Actual365Fixed().yearFraction(curve.referenceDate(), date)
        times.append(t)
        discount_factors.append(
            curve.forwardRate(
                date,
                ql.TARGET().advance(date, 1, ql.Months),
                ql.Actual360(),
                ql.Simple,
            ).rate()
        )

    # Plotting the curve using schedule
    plt.figure(figsize=(10, 6))
    plt.plot(
        times,
        discount_factors,
        label="Discount Curve (Scheduled)",
        color="blue",
        lw=2,
    )
    plt.title("Piecewise Log-Cubic Discount Curve with Schedule")
    plt.xlabel("Years")
    plt.ylabel("Discount Factor")
    plt.grid(True)
    plt.legend()
    plt.show()


def get_ql_quotes_periods(data):
    entries = data.to_dict(orient="records")
    res = []
    for entry in entries:
        tenor = entry["tenor"]
        ql_quote_handle = ql.QuoteHandle(
            ql.SimpleQuote(float(entry["rate"]) / 100)
        )
        ql_period = ql.Period(tenor)
        res.append((ql_quote_handle, ql_period))
    return res
