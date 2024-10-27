import QuantLib as ql
from pypika import Order, Query, Table

from finance.db import query_db


async def get_fixings(
    index_name, index=None, tenor=None, up_to=None, starting_at=None
):
    table = Table("taxa_fixa_fixings_historical")
    query = (
        Query.from_(table)
        .select(table.date, table.rate)
        .where(table.index_name == index_name)
    )
    if tenor:
        query = query.where(table.tenor == tenor)
    if index:
        query = query.where(table.index == index)
    if up_to:
        query = query.where(table.date <= up_to)
    if starting_at:
        query = query.where(table.date > starting_at)
    query = query.orderby(table.date, order=Order.asc)
    return await query_db(str(query))


async def apply_fixings(index, calendar, deposit_rate, index_name=None):
    fixings = await get_fixings(index_name, index)
    return add_fixings_to_curve(calendar, deposit_rate, fixings)


def add_fixings_to_curve(calendar, deposit_rate, all_fixings):
    # Iterate over each fixing
    fixing_dates = []
    fixing_rates = []
    last_rate = None
    fixings = all_fixings.to_dict(orient="records")
    for row in fixings:
        date = row["date"]
        rate = row["rate"]
        date_ql = ql.Date(date.day, date.month, date.year)
        if calendar.isBusinessDay(date_ql):
            last_rate = rate
            fixing_dates.append(date_ql)
            fixing_rates.append(rate / 100)
    try:
        deposit_rate.addFixings(
            fixing_dates, fixing_rates, forceOverwrite=True
        )
    except Exception as e:
        print(f"Error adding bulk fixings: {str(e)}")
    return  last_rate
