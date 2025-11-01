from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from tools.logger_config import logger


def get_connection_pool(db_url: str):
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
        "application_name": "cosmos",
    }

    conn_pool = ConnectionPool(
        conninfo=db_url,
        kwargs=connection_kwargs,
        min_size=1,
        max_size=4,
        max_idle=60 * 2,
    )
    return conn_pool