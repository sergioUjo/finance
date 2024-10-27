"""CLI interface for finance project.

Be creative! do whatever you want!

- Install click or typer and create a CLI app
- Use builtin argparse
- Start a web application
- Import things from your .base module
"""

import asyncio

import matplotlib.pyplot as plt

from finance.calibrate import fill_missing_dates
from finance.db import close_db_pool
from finance.euribor_6m import curve
from finance.fixings import get_fixings
from finance.utils import curve_values


# Database connection string

# Global variable for connection pool


def main():  # pragma: no cover
    """
    The main function executes on commands:
    `python -m finance` and `$ finance `.

    This is your program's entry point.

    You can change this function to do whatever you want.
    Examples:
        * Run a test suite
        * Run a server
        * Do some other stuff
        * Run a command line application (Click, Typer, ArgParse)
        * List all available tasks
        * Run an application (Flask, FastAPI, Django, etc.)
    """
    asyncio.run(show())
    asyncio.run(close_db_pool())


import pandas as pd
import numpy as np
import QuantLib as ql
from scipy.optimize import minimize


async def show():
    # Step 1: Load Historical Euribor Data (fixings)
    # Assuming df contains historical 6M Euribor fixings with 'date' and 'rate' columns
    df = await get_fixings("EURIBOR", "6M")
    df["rate"] = df["rate"] / 100
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by='date')
    fixings_df = fill_missing_dates(df)
    # Convert 'date' column to QuantLib Date format
    fixings_df['QL_Date'] = fixings_df['date'].apply(lambda d: ql.Date(d.day, d.month, d.year))

    euribor =await curve()

    # Use a flat rate term structure (or replace with a more complex structure if you have one)
    rate_handle = ql.YieldTermStructureHandle(euribor)

    todaysDate = euribor.referenceDate()

    # Define the Hull-White short-rate model's error function based on historical fixings
    def hull_white_model_error(params):
        a, sigma = params  # Extract Hull-White model parameters

        # Create a Hull-White process with the current 'a' and 'sigma'
        hw_process = ql.HullWhiteProcess(rate_handle, a, sigma)

        # Accumulate the squared error between model and historical fixings
        error = 0.0
        for i, row in fixings_df.iterrows():
            historical_date = row['QL_Date']
            historical_rate = row['rate']

            # Time difference from the evaluation date to the historical fixing date
            if historical_date < todaysDate:
                # Historical date is earlier, use historical_date as first argument
                t = ql.Actual365Fixed().yearFraction(historical_date, todaysDate)
            else:
                # Historical date is later, reverse the order
                t = ql.Actual365Fixed().yearFraction(todaysDate, historical_date)
            # Simulate the short rate at the historical fixing date using the Hull-White model
            short_rate = hw_process.expectation(0, 0, t)  # Expectation of short rate at time t

            # Calculate squared error between the model's rate and the actual historical rate
            error += (short_rate - historical_rate) ** 2

        return np.sqrt(error)  # Return the root mean square error as the objective function

    # Initial guess for the parameters (a, sigma)
    initial_guess = [0.03, 0.001]

    # Minimize the error function to find the best-fit parameters
    result = minimize(hull_white_model_error, initial_guess, method='L-BFGS-B', bounds=[(0, None), (0, None)])

    # Extract the calibrated parameters
    calibrated_a, calibrated_sigma = result.x
    print(f"Calibrated a: {calibrated_a}, Calibrated sigma: {calibrated_sigma}")
    # Create the Hull-White process
    hw_process = ql.HullWhiteProcess(rate_handle, calibrated_a, calibrated_sigma)


    time_grid = ql.TimeGrid(30.0, 365 * 8)
    # Gaussian random sequence and path generator
    rng = ql.GaussianRandomSequenceGenerator(
        ql.UniformRandomSequenceGenerator(len(time_grid) - 1, ql.UniformRandomGenerator()))
    seq = ql.GaussianPathGenerator(hw_process, time_grid, rng, False)

    # Step 3: Simulate paths
    num_paths = 600  # Number of paths to simulate
    simulated_paths = []

    for i in range(num_paths):
        sample_path = seq.next()
        path = sample_path.value()
        time_points = [path.time(j) for j in range(len(path))]
        rates = [path[j] for j in range(len(path))]
        dates,payments= calculate_mortgage_payments(rates, time_points,145000, 30, )
        simulated_paths.append((dates, rates))

    curve_rates, curve_times = curve_values(euribor)
    #curve_times= calculate_mortgage_payments(145000, 30, curve_times, curve_rates)

    # Step 4: Plot the simulated paths
    plt.figure(figsize=(10, 6))
    all_rates = np.array([rates for _, rates in simulated_paths])
    time_points = [time for time, _ in simulated_paths]
    p5 = np.percentile(all_rates, 20, axis=0)  # 5th percentile
    p95 = np.percentile(all_rates, 80, axis=0)  # 95th percentile
    # Plot the P5, P50, and P95 lines


    for i, (time_points, rates) in enumerate(simulated_paths):
        plt.plot(time_points, rates, label=f'Path {i + 1}',lw=0.1, alpha=0.5)
    plt.fill_between(time_points, p5, p95, color='red', alpha=0.7, label='P5 to P95 Range')
  #  plt.plot(
   #     curve_rates,        curve_times,

  #      label="Actual curve",
   #     color="blue",
  #      lw=2,
  #  )
    plt.title('Simulated Hull-White Short Rate Paths')
    plt.xlabel('Time (Years)')
    plt.ylabel('Short Rate')
    plt.legend()
    plt.grid(True)
    plt.show()


def calculate_mortgage_payments(rates, rate_dates, principal, years):
    # Define the calendar and the day counter (for European mortgages, TARGET and Actual/360 is common)
    calendar = ql.TARGET()
    day_counter = ql.Actual360()
    #rate date is a float so we need to convert it to a date
    rate_dates = [pd.to_datetime(d) for d in rate_dates]

    df = pd.DataFrame({'date': rate_dates, 'rate': rates})
    ## remove duplicates on date column
    df = df.drop_duplicates(subset=['date'])
    dates = df['date']
    ql_rate_dates = [ql.Date(d.day, d.month, d.year) for d in dates]

    rates = df['rate']
    # Create a yield curve from the provided dates and rates
    rate_helpers = [
        ql.DepositRateHelper(ql.QuoteHandle(ql.SimpleQuote(rate / 100.0)),
                             ql.Period(6, ql.Months),
                             2,
                             calendar,
                             ql.ModifiedFollowing,
                             False,
                             day_counter)
        for rate in rates
    ]

    yield_curve = ql.PiecewiseLinearZero(
        0, calendar, rate_helpers, day_counter
    )

    # Mortgage schedule setup (monthly payments)
    start_date = ql_rate_dates[0]  # Start from the first provided rate date
    end_date = start_date + ql.Period(years * 12, ql.Months)  # Total years in months

    # Define a schedule for monthly payments
    schedule = ql.Schedule(
        start_date,
        end_date,
        ql.Period(ql.Monthly),
        calendar,
        ql.ModifiedFollowing,
        ql.ModifiedFollowing,
        ql.DateGeneration.Forward,
        False
    )

    # Calculate the total number of payments (for each month over the years)
    total_months = years * 12

    # Define lists to store payment dates and amounts
    payment_dates = []
    payments = []

    # Initial principal to be repaid
    remaining_principal = principal

    # Iterate over the months in the payment schedule
    for i, payment_date in enumerate(schedule):
        if i >= total_months:
            break  # Stop after the number of months needed

        # Get the appropriate forward rate from the yield curve for this period
        rate = yield_curve.forwardRate(payment_date, payment_date + ql.Period(1, ql.Months), day_counter,
                                       ql.Simple).rate()

        # Calculate monthly interest based on the current rate
        monthly_interest = rate / 12.0

        # Calculate monthly payment using annuity formula for remaining principal
        total_payment = remaining_principal * monthly_interest / (1 - (1 + monthly_interest) ** -total_months)

        # Update the remaining principal after the payment
        remaining_principal -= (total_payment - remaining_principal * monthly_interest)

        # Append the date and payment amount to the respective arrays
        payment_dates.append(payment_date)
        payments.append(total_payment)

        # Stop if the principal is fully repaid
        if remaining_principal <= 0:
            break

    return payment_dates, payments
