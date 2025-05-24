import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
from ytindexer.config import settings
from ytindexer.logging import logger
from .base import AsyncDatabaseConnection


class MongoConnection(AsyncDatabaseConnection[AsyncIOMotorClient]):
    """
    Concrete implementation of AsyncDatabaseConnection for MongoDB using Motor.

    Args:
        dsn (str): MongoDB connection string.
    """

    def __init__(self, dsn: str):
        self.dsn = dsn
        self._client: AsyncIOMotorClient | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> AsyncIOMotorClient:
        """
        Establish and return an AsyncIOMotorClient instance.

        Returns:
            AsyncIOMotorClient: The async MongoDB client.

        Raises:
            ConnectionFailure: If connection to MongoDB fails.
        """
        async with self._lock:
            if self._client is None:
                try:
                    self._client = AsyncIOMotorClient(self.dsn)
                    # Optionally test connection by pinging
                    await self._client.admin.command('ping')
                    logger.info("Successfully connected to MongoDB at: {host}", host=self.dsn)
                except ConnectionFailure as conn_fail:
                    logger.error("Couldn't connect to the MongoDB database: {error}", error=conn_fail)
                    raise
            return self._client

    async def close(self) -> None:
        """
        Close the MongoDB client connection.
        """
        async with self._lock:
            if self._client is not None:
                self._client.close()
                self._client = None