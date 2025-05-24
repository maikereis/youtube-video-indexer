import time
import traceback
from typing import Any, Dict

from ytindexer.logging import logger

from .config import ElasticsearchConfig, RetryConfig
from .health import HealthCheckable, HealthStatus
from .results import OperationResult
from .retry import RetryableOperation


class SearchIndexingService(HealthCheckable):
    """Handles video search indexing in Elasticsearch"""
    
    def __init__(self, client: Any, config: ElasticsearchConfig, retry_config: RetryConfig):
        self.client = client
        self.config = config
        self.retry = RetryableOperation(retry_config)
        logger.info("Initialized SearchIndexingService")

    async def ensure_index(self) -> OperationResult:
        """Create Elasticsearch index if it doesn't exist"""
        try:
            if not await self.client.indices.exists(index=self.config.index_name):
                await self.client.indices.create(
                    index=self.config.index_name, 
                    body=self.config.mapping
                )
                logger.info(f"Created Elasticsearch index: {self.config.index_name}")
                return OperationResult.success(f"Created index: {self.config.index_name}")
            else:
                return OperationResult.success(f"Index already exists: {self.config.index_name}")
        except Exception as e:
            logger.error(f"Failed to ensure index: {str(e)}")
            return OperationResult.failure(f"Failed to ensure index: {str(e)}", e)

    async def index_video(self, video_data: Dict[str, Any]) -> OperationResult:
        """Index video metadata in Elasticsearch with retry logic"""
        video_id = video_data.get("video_id")
        if not video_id:
            return OperationResult.failure("Video data missing video_id")
        
        async def _index_operation():
            await self.client.index(
                index=self.config.index_name,
                id=video_id,
                body=video_data,
                refresh=True
            )
            return video_id
        
        try:
            result_id = await self.retry.execute(_index_operation, f"index_video_{video_id}")
            logger.debug(f"Indexed video in Elasticsearch: {result_id}")
            return OperationResult.success(
                f"Indexed video: {result_id}",
                metadata={"video_id": result_id}
            )
        except Exception as e:
            logger.error(f"Failed to index video in Elasticsearch: {str(e)}")
            logger.debug(traceback.format_exc())
            return OperationResult.failure(f"Failed to index video: {str(e)}", e)

    async def health_check(self) -> HealthStatus:
        """Check Elasticsearch cluster health"""
        start_time = time.time()
        try:
            health = await self.client.cluster.health()
            response_time = (time.time() - start_time) * 1000
            
            is_healthy = health.get('status') in ['green', 'yellow']
            message = f"Cluster status: {health.get('status', 'unknown')}"
            
            return HealthStatus(
                service_name="elasticsearch",
                is_healthy=is_healthy,
                response_time_ms=response_time,
                message=message,
                metadata=health
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthStatus(
                service_name="elasticsearch",
                is_healthy=False,
                response_time_ms=response_time,
                message=f"Health check failed: {str(e)}"
            )

    async def close(self):
        """Close the Elasticsearch client"""
        await self.client.close()