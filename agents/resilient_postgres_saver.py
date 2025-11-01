import time
from typing import Optional

from langgraph.checkpoint.postgres import Conn, PostgresSaver
from langgraph.checkpoint.serde.base import SerializerProtocol
from psycopg import Connection, Pipeline
from psycopg.errors import OperationalError
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from agents.postgres import get_connection_pool
from tools.logger_config import logger as logging


class ResilientPostgresSaver(PostgresSaver):
    def __init__(
        self,
        conn: Conn,
        pipe: Optional[Pipeline] = None,
        serde: Optional[SerializerProtocol] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,  # seconds
    ) -> None:
        super().__init__(conn, pipe, serde)
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _execute_with_retries(self, query_func, *args, **kwargs):
        retries = 0
        while retries < self.max_retries:
            try:
                return query_func(*args, **kwargs)
            except (OperationalError, ConnectionError) as e:
                logging.error(
                    f"Database operation failed: {e}, retrying...", exc_info=True
                )
                retries += 1
                if retries >= self.max_retries:
                    raise
                time.sleep(self.retry_delay)
                self._reconnect()

    def _reconnect(self):
        try:
            self.conn.close()
        except Exception as e:
            logging.exception(f"Error closing connection {e}", exc_info=True)

        if isinstance(self.conn, ConnectionPool):
            logging.info(f"Reinitializing connection pool for {self.conn.conninfo}")
            try:
                self.conn = get_connection_pool(self.conn.conninfo)
            except Exception as e:
                logging.exception(
                    f"Error reinitializing connection pool {e}", exc_info=True
                )
        else:
            try:
                self.conn = Connection.connect(
                    self.conn.conninfo,
                    autocommit=True,
                    prepare_threshold=0,
                    row_factory=dict_row,
                )
            except Exception as e:
                logging.exception(f"Error reconnecting {e}", exc_info=True)

    def setup(self) -> None:
        self._execute_with_retries(super().setup)

    def list(self, *args, **kwargs):
        return self._execute_with_retries(super().list, *args, **kwargs)

    def get_tuple(self, *args, **kwargs):
        return self._execute_with_retries(super().get_tuple, *args, **kwargs)

    def put(self, *args, **kwargs):
        return self._execute_with_retries(super().put, *args, **kwargs)

    def put_writes(self, *args, **kwargs):
        return self._execute_with_retries(super().put_writes, *args, **kwargs)