from elasticsearch import AsyncElasticsearch

from ytindexer.config import settings
from ytindexer.logging import logger


class ElasticConnection:
    _instance: AsyncElasticsearch | None = None

    def __new__(cls, *args, **kwargs) -> AsyncElasticsearch:
        if cls._instance is None:
            try:
                cls._instance = AsyncElasticsearch(settings.search.dsn)
            except valkey.exceptions.ConnectionError as conn_fail:
                logger.error("Couldn't connect to the Elastic: {error}", error=conn_fail)
                raise

        logger.info(
            "Successfully connected to Elastic at: {host}", host=settings.valkey.host
        )
        return cls._instance