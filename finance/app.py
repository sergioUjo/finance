from datetime import datetime

import QuantLib as ql
from dateutil.relativedelta import relativedelta
from fastapi import FastAPI
from mangum import Mangum

from finance import euribor
from finance.utils import curve_values

app = FastAPI()

@app.get("/forward_curve")
async def calculate_forward_curve(index):

    curve = await euribor.curve(index)


    return curve_values(curve,index)


@app.get("/forward_rates")
async def forward_rates(index):
    # Get the curve object
    curve = await euribor.curve(index)


    # Define a list of dates for January 1st of the next 5 years
    jan_1st_dates = [(datetime.now() + relativedelta(years=i)).replace(month=1, day=1) for i in range(1, 6)]

    # Extract values for these dates and prepare the response
    forward_values = []
    for date in jan_1st_dates:
        rate = curve_forward_rate(curve, date,index)  # Assuming a function to extract the forward rate for a specific date
        forward_values.append({
            "time": date,
            "rate": rate
        })

    return forward_values


def curve_forward_rate(curve, target_date, tenor="1M"):
    """
    Calculate the forward rate for a given target date using QuantLib and a specific tenor.
    """
    # Convert Python date to QuantLib Date
    ql_target_date = ql.Date(target_date.day, target_date.month, target_date.year)

    ql_tenor_period =  ql.Period(tenor)

    # Define start and end dates for the forward rate calculation
    start_date = ql_target_date
    end_date = ql_target_date + ql_tenor_period  # Use the specified tenor period

    # Calculate the annualized forward rate
    forward_rate = curve.forwardRate(start_date, end_date, ql.Actual360(), ql.Simple).rate()

    return forward_rate

handler = Mangum(app)