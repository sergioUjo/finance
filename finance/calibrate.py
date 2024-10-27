import QuantLib as ql
import numpy as np
import pandas as pd


def calculate_volatility(df):
    """
    Calculate historical volatility of Euribor fixings over a given period.

    Parameters:
    df (pd.DataFrame): DataFrame containing 'Date' and 'Rate' columns for Euribor fixings.
    start_date (str): Start date for the period (format: 'YYYY-MM-DD'). Default is None (use entire range).
    end_date (str): End date for the period (format: 'YYYY-MM-DD'). Default is None (use entire range).

    Returns:
    float: Annualized volatility of the log returns of Euribor fixings.
    """
    # Sort data by date just to be sure
    df = df.sort_values(by="date")
    df = fill_missing_dates(df)
    # Calculate log returns
    df["Log Return"] = np.log(df["rate"] / df["rate"].shift(1))

    # Drop NaN values resulting from shift
    df = df.dropna()

    window_size_1Y = 252  # 1 year (252 trading days)
    window_size_2Y = 504  # 2 years
    window_size_5Y = 1260  # 5 years
    window_size_10Y = 2520  # 10 years
    window_size_15Y = 3780  # 15 years
    window_size_20Y = 5040  # 20 years

    # Estimate volatility (annualized) using a rolling window
    df["Volatility_1Y"] = df["Log Return"].rolling(
        window=window_size_1Y
    ).std() * np.sqrt(252)
    df["Volatility_2Y"] = df["Log Return"].rolling(
        window=window_size_2Y
    ).std() * np.sqrt(252)
    df["Volatility_5Y"] = df["Log Return"].rolling(
        window=window_size_5Y
    ).std() * np.sqrt(252)
    df["Volatility_10Y"] = df["Log Return"].rolling(
        window=window_size_10Y
    ).std() * np.sqrt(252)
    df["Volatility_15Y"] = df["Log Return"].rolling(
        window=window_size_15Y
    ).std() * np.sqrt(252)
    df["Volatility_20Y"] = df["Log Return"].rolling(
        window=window_size_20Y
    ).std() * np.sqrt(252)
    # Drop NaN values after rolling calculations
    df = df.dropna()
    # Create a DataFrame to hold the volatility surface
    volatility_surface = pd.DataFrame(
        {
            "Date": df["date"],
            "1Y Volatility": df["Volatility_1Y"],
            "2Y Volatility": df["Volatility_2Y"],
            "5Y Volatility": df["Volatility_5Y"],
            "10Y Volatility": df["Volatility_10Y"],
            "15Y Volatility": df["Volatility_15Y"],
            "20Y Volatility": df["Volatility_20Y"],
        }
    )
    # Drop NaN values
    volatility_surface = volatility_surface.dropna()
    return volatility_surface


def fill_missing_dates(df):
    df.set_index("date", inplace=True)

    # Create a date range covering all dates between the min and max date in your DataFrame
    full_date_range = pd.date_range(df.index.min(), df.index.max())

    # Reindex the DataFrame to include all the dates in the range
    df = df.reindex(full_date_range)

    # Forward fill the missing rate values
    df_filled = df.ffill()

    # If you want to reset the index to bring 'date' back as a column
    df_filled = df_filled.reset_index().rename(columns={"index": "date"})
    return df_filled


def simulate_hw_paths(hw_model, forward_curve, maturity_years, num_paths=100, num_steps=252):
    """
    Simulate Hull-White paths and estimate model-implied volatility.

    Parameters:
    hw_model (QuantLib.HullWhite): Hull-White model object.
    forward_curve (QuantLib.YieldTermStructureHandle): Forward curve for the model.
    maturity_years (int): Maturity for which to simulate paths (1Y, 2Y, etc.).
    num_paths (int): Number of Monte Carlo paths.
    num_steps (int): Number of time steps.

    Returns:
    float: Model-implied volatility.
    """
    # Create the Hull-White process
    hw_process = ql.HullWhiteProcess(forward_curve, hw_model.params()[0], hw_model.params()[1])

    # Time step for the simulation
    maturity_time = maturity_years

    # Initialize path generator
    rng = ql.GaussianRandomSequenceGenerator(
        ql.UniformRandomSequenceGenerator(num_steps, ql.UniformRandomGenerator())
    )
    seq = ql.GaussianPathGenerator(hw_process, maturity_time, num_steps, rng, False)

    # Simulate paths and collect the final rates
    paths = []
    for i in range(num_paths):
        sample_path = seq.next()
        path = sample_path.value()
        paths.append(path[-1])

    # Estimate the model-implied volatility (standard deviation of log returns)
    paths = np.array(paths)
    log_returns = np.log(paths[1:] / paths[:-1])
    return np.std(log_returns) * np.sqrt(252)  # Annualized volatility


def calibration_error(params, hw_model, forward_curve, volatility_surface):
    """
    Objective function to minimize during calibration. Compares historical volatilities
    with model-implied volatilities for different maturities.

    Parameters:
    params (list): List of Hull-White parameters [a, sigma].
    hw_model (QuantLib.HullWhite): Hull-White model.
    forward_curve (QuantLib.YieldTermStructureHandle): Forward curve.
    volatility_surface (pd.DataFrame): Historical volatility surface.

    Returns:
    float: Sum of squared errors between historical and model-implied volatilities.
    """
    a, sigma = params
    hw_model.setParams([a, sigma])  # Update Hull-White parameters

    error = 0
    # Loop over each maturity in the volatility surface
    for maturity_years in [1, 2, 5, 10, 15, 20]:
        historical_vol = volatility_surface[f'{maturity_years}Y Volatility'].mean()  # Average historical vol
        model_vol = simulate_hw_paths(hw_model, forward_curve, maturity_years)  # Model-implied vol
        error += (historical_vol - model_vol) ** 2  # Sum of squared errors

    return error
