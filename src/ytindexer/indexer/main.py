import asyncio
from datetime import datetime, timezone

from ytindexer.config import settings
from ytindexer.database import (ElasticConnection, MongoConnection,
                                ValkeyConnection)
from ytindexer.indexer import (ChannelStatsService, ElasticsearchConfig,
                               MongoDBConfig, RetryConfig,
                               SearchIndexingService, VideoIndexingProcessor,
                               VideoStorageService)
from ytindexer.indexer.results import OperationStatus
from ytindexer.logging import logger
from ytindexer.queues import NotificationQueue


# Example configuration and setup
async def main():
    # Configuration
    es_config = ElasticsearchConfig(index_name="videos", shards=2, replicas=1)

    mongo_config = MongoDBConfig(
        database_name=settings.mongo.name,
        videos_collection="videos",
        channels_collection="channels",
    )

    retry_config = RetryConfig(max_attempts=3, base_delay=1.0, max_delay=30.0)

    valkey_client = ValkeyConnection(
            host=settings.valkey.host,
            port=settings.valkey.port,
            password=settings.valkey.password.get_secret_value(),
        )
    es_client = ElasticConnection(settings.search.dsn)
    mongo_client = MongoConnection(settings.mongo.dsn)

    valkey_conn = await valkey_client.connect()
    es_conn = await es_client.connect()
    mongo_conn = await mongo_client.connect()

    # Initialize services with configuration
    output_queue = NotificationQueue(valkey_conn, "output-queue")
    storage_service = VideoStorageService(mongo_conn, mongo_config, retry_config)
    search_service = SearchIndexingService(es_conn, es_config, retry_config)
    stats_service = ChannelStatsService(mongo_conn, mongo_config, retry_config)

    # Initialize processor
    processor = VideoIndexingProcessor(
        input_queue=output_queue,
        video_storage=storage_service,
        search_indexing=search_service,
        channel_stats=stats_service,
    )

    # Ensure all indices are created
    indices_result = await processor.ensure_indices()

    if indices_result.is_failure:
        logger.error(f"Failed to ensure indices: {indices_result.message}")
        return

    await processor.run()

    # Periodic health checks during operation
    while True:
        health = await processor.health_check()
        if not health.is_healthy:
            logger.warning(f"Health check failed: {health.message}")
            # Could implement alerting here

        await asyncio.sleep(30)  # Check every 30 seconds


if __name__ == "__main__":
    asyncio.run(main())
