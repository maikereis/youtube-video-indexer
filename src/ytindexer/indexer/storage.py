import time
import traceback
from datetime import datetime, timezone
from typing import Any, Dict

from pymongo.errors import DuplicateKeyError, OperationFailure

from ytindexer.logging import logger

from .config import MongoDBConfig, RetryConfig
from .health import HealthCheckable, HealthStatus
from .results import OperationResult
from .retry import RetryableOperation


class VideoStorageService(HealthCheckable):
    """Handles video metadata storage in MongoDB"""

    def __init__(self, client: Any, config: MongoDBConfig, retry_config: RetryConfig):
        self.client = client
        self.config = config
        self.retry = RetryableOperation(
            retry_config, non_retry_exceptions=[DuplicateKeyError]
        )
        self.db = self.client[config.database_name]
        self.videos_collection = self.db[config.videos_collection]
        logger.info("Initialized VideoStorageService")

    async def ensure_indices(self) -> OperationResult:
        """Ensure the required database indices exist"""
        created_indexes = []
        failed_indexes = []

        for index_name, index_config in self.config.video_indexes.items():
            try:
                await self.videos_collection.create_index(index_name, **index_config)
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
                metadata={"created": created_indexes, "failed": failed_indexes},
            )
        else:
            return OperationResult.success(
                f"Ensured indexes: {created_indexes}",
                metadata={"indexes": created_indexes},
            )

    async def store_video(self, video_data: Dict[str, Any]) -> OperationResult:
        """Store video metadata in MongoDB with retry logic"""
        video_id = video_data.get("video_id")
        if not video_id:
            return OperationResult.failure("Video data missing video_id")

        async def _store_operation():
            result = await self.videos_collection.update_one(
                {"video_id": video_id},
                {"$set": {**video_data, "updated_at": datetime.now(timezone.utc)}},
                upsert=True,
            )
            return result

        try:
            result = await self.retry.execute(
                _store_operation, f"store_video_{video_id}"
            )
            logger.debug(f"Stored video in MongoDB: {video_id}")

            action = "updated" if result.matched_count > 0 else "inserted"

            return OperationResult.success(
                f"Video {action}: {video_id}",
                metadata={"video_id": video_id, "action": action},
            )
        except Exception as e:
            logger.error(f"Failed to store video in MongoDB: {str(e)}")
            logger.debug(traceback.format_exc())
            return OperationResult.failure(f"Failed to store video: {str(e)}", e)

    async def health_check(self) -> HealthStatus:
        """Check MongoDB connection health"""
        start_time = time.time()
        try:
            # Simple ping to check connection
            await self.client.admin.command("ping")
            response_time = (time.time() - start_time) * 1000

            return HealthStatus(
                service_name="mongodb",
                is_healthy=True,
                response_time_ms=response_time,
                message="Connection healthy",
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthStatus(
                service_name="mongodb",
                is_healthy=False,
                response_time_ms=response_time,
                message=f"Health check failed: {str(e)}",
            )
