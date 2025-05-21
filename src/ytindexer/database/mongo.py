from motor.motor_asyncio import AsyncIOMotorClient
from ytindexer.config import settings
from ytindexer.logging import logger

class MongoConnection:
    _instance: AsyncIOMotorClient | None = None

    def __new__(cls, *args, **kwargs) -> AsyncIOMotorClient:
        if cls._instance is None:
            try:
                cls._instance = AsyncIOMotorClient(settings.mongo.dsn)
            except ConnectionFailure as conn_fail:
                logger.error("Couldn't connect to the MongoDB database: {error}", error=conn_fail)
                raise

        logger.info("Successfully connected to Mongo at: {host}", host=settings.mongo.host)
        return cls._instance