import aiopg
import pandas as pd

DATABASE_URL = "postgresql://default_owner:H6oWO5FkKsiu@ep-hidden-frost-a2991b2t.eu-central-1.aws.neon.tech/default?sslmode=require"
pool = None


async def init_db_pool():
    """Initialize the database connection pool once."""
    global pool
    if pool is None:
        pool = await aiopg.create_pool(DATABASE_URL)


async def close_db_pool():
    """Close the database connection pool."""
    global pool
    if pool is not None:
        pool.close()
        await pool.wait_closed()


async def query_db(query, args=None):
    print(f"Executing query: {query}")
    await init_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            if args is None:
                await cur.execute(query)
            else:
                await cur.execute(query, args)
            data = await cur.fetchall()
            columns = [
                desc[0] for desc in cur.description
            ]  # Fetch column names from description
            return pd.DataFrame(data, columns=columns)
