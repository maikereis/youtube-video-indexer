import asyncio
from elasticsearch import AsyncElasticsearch, ConnectionError
from ytindexer.config import settings
from ytindexer.logging import logger
from .base import AsyncDatabaseConnection


class ElasticConnection(AsyncDatabaseConnection[AsyncElasticsearch]):
    """
    Concrete implementation of AsyncDatabaseConnection for ElasticSearch.

    Args:
        dsn (str): The connection string or DSN for ElasticSearch.
    """

    def __init__(self, dsn: str):
        self.dsn = dsn
        self._client: AsyncElasticsearch | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> AsyncElasticsearch:
        """
        Establish and return an AsyncElasticsearch client instance.

        Returns:
            AsyncElasticsearch: The ElasticSearch async client.
        
        Raises:
            ConnectionError: If connection to ElasticSearch fails.
        """
        async with self._lock:
            if self._client is None:
                try:
                    self._client = AsyncElasticsearch(self.dsn)
                    logger.info("Successfully connected to Elastic at: {host}", host=self.dsn)
                except ConnectionError as conn_fail:
                    logger.error("Couldn't connect to Elastic: {error}", error=conn_fail)
                    raise
            return self._client

    async def close(self) -> None:
        """
        Close the AsyncElasticsearch client connection.
        """
        async with self._lock:
            if self._client is not None:
                await self._client.close()
                self._client = None
