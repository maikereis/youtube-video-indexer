import asyncio

import valkey
from ytindexer.config import settings
from ytindexer.logging import logger
from .base import AsyncDatabaseConnection


class ValkeyConnection(AsyncDatabaseConnection[valkey.client.Valkey]):
    """
    Concrete implementation of AsyncDatabaseConnection for Valkey client.

    Args:
        host (str): Valkey host address.
        port (int): Valkey port.
        password (str): Password for Valkey authentication.
    """

    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.port = port
        self.password = password
        self._client: valkey.client.Valkey | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> valkey.client.Valkey:
        """
        Establish and return a Valkey client connection.

        Returns:
            valkey.client.Valkey: The Valkey client instance.

        Raises:
            valkey.exceptions.ConnectionError: If connection to Valkey fails.
        """
        async with self._lock:
            if self._client is None:
                try:
                    self._client = valkey.Valkey(
                        host=self.host,
                        port=self.port,
                        username=None,
                        password=self.password,
                        db=0,
                    )
                    self._client.ping()
                    logger.info("Successfully connected to Valkey at: {host}", host=self.host)
                except valkey.exceptions.ConnectionError as conn_fail:
                    logger.error("Couldn't connect to the Valkey: {error}", error=conn_fail)
                    raise
            return self._client

    async def close(self) -> None:
        """
        Close the Valkey client connection.
        """
        async with self._lock:
            if self._client is not None:
                self._client.close()
                self._client = None