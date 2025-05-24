import time
import traceback
from datetime import datetime, timezone
from typing import Any, Dict

from pymongo.errors import OperationFailure

from ytindexer.logging import logger

from .config import MongoDBConfig, RetryConfig
from .health import HealthCheckable, HealthStatus
from .results import OperationResult
from .retry import RetryableOperation


class ChannelStatsService(HealthCheckable):
    """Handles channel statistics updates"""
    
    def __init__(self, client: Any, config: MongoDBConfig, retry_config: RetryConfig):
        self.client = client
        self.config = config
        self.retry = RetryableOperation(retry_config)
        self.db = self.client[config.database_name]
        self.channels_collection = self.db[config.channels_collection]
        logger.info("Initialized ChannelStatsService")

    async def ensure_indices(self) -> OperationResult:
        """Ensure the required database indices exist"""
        created_indexes = []
        failed_indexes = []
        
        for index_name, index_config in self.config.channel_indexes.items():
            try:
                await self.channels_collection.create_index(index_name, **index_config)
                created_indexes.append(index_name)
                logger.debug(f"Created index: {index_name}")
            except OperationFailure as e:
                if "already exists" in str(e):
                    logger.debug(f"Index '{index_name}' already exists")
                    created_indexes.append(index_name)
                else:
                    failed_indexes.append(index_name)
                    logger.error(f"Failed to create index {index_name}: {str(e)}")
        
        if failed_indexes:
            return OperationResult.failure(
                f"Failed to create indexes: {failed_indexes}",
                metadata={"created": created_indexes, "failed": failed_indexes}
            )
        else:
            return OperationResult.success(
                f"Ensured indexes: {created_indexes}",
                metadata={"indexes": created_indexes}
            )

    async def update_channel_stats(self, video_data: Dict[str, Any]) -> OperationResult:
        """Update channel statistics based on video data with retry logic"""
        channel_id = video_data.get("channel_id")
        if not channel_id:
            return OperationResult.failure("Video data missing channel_id")
        
        async def _update_operation():
            result = await self.channels_collection.update_one(
                {"channel_id": channel_id},
                {
                    "$inc": {"video_count": 1},
                    "$set": {"last_activity": datetime.now(timezone.utc)},
                    "$setOnInsert": {"first_seen": datetime.now(timezone.utc)}
                },
                upsert=True
            )
            return result
        
        try:
            result = await self.retry.execute(_update_operation, f"update_channel_stats_{channel_id}")
            logger.debug(f"Updated channel stats: {channel_id}")
            
            action = "updated" if result.matched_count > 0 else "created"
            return OperationResult.success(
                f"Channel stats {action}: {channel_id}",
                metadata={"channel_id": channel_id, "action": action}
            )
        except Exception as e:
            logger.error(f"Failed to update channel stats: {str(e)}")
            logger.debug(traceback.format_exc())
            return OperationResult.failure(f"Failed to update channel stats: {str(e)}", e)

    async def health_check(self) -> HealthStatus:
        """Check MongoDB connection health for channels collection"""
        start_time = time.time()
        try:
            # Test access to channels collection
            await self.channels_collection.count_documents({}, limit=1)
            response_time = (time.time() - start_time) * 1000
            
            return HealthStatus(
                service_name="mongodb_channels",
                is_healthy=True,
                response_time_ms=response_time,
                message="Channels collection accessible"
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthStatus(
                service_name="mongodb_channels", 
                is_healthy=False,
                response_time_ms=response_time,
                message=f"Health check failed: {str(e)}"
            )