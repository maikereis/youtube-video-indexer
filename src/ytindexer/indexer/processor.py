import asyncio
import time
from typing import Any, Dict, List, Optional

from ytindexer.logging import logger
from ytindexer.queues import Queue

from .health import HealthCheckable, HealthStatus
from .indexing import SearchIndexingService
from .results import OperationResult, OperationStatus, ProcessingResult
from .stats import ChannelStatsService
from .storage import VideoStorageService


class VideoIndexingProcessor(HealthCheckable):
    """Orchestrates the video indexing process with enhanced error handling and health checks"""
    
    def __init__(self, input_queue: Queue, video_storage: VideoStorageService, 
                 search_indexing: SearchIndexingService, channel_stats: ChannelStatsService,
                 max_concurrent_tasks: int = 10, poll_interval: float = 1.0):
        self.input_queue = input_queue
        self.video_storage = video_storage
        self.search_indexing = search_indexing
        self.channel_stats = channel_stats
        self.max_concurrent_tasks = max_concurrent_tasks
        self.poll_interval = poll_interval
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._active_tasks: set = set()
        logger.info("Initialized VideoIndexingProcessor")

    async def ensure_indices(self) -> OperationResult:
        """Ensure all required database indices and mappings exist"""
        results = []
        
        storage_result = await self.video_storage.ensure_indices()
        results.append(("storage", storage_result))
        
        indexing_result = await self.search_indexing.ensure_index()
        results.append(("indexing", indexing_result))
        
        stats_result = await self.channel_stats.ensure_indices()
        results.append(("stats", stats_result))

        logger.info(results)
        
        failed_services = [name for name, result in results if result.is_failure]
        
        if failed_services:
            return OperationResult.failure(
                f"Failed to ensure indices for: {failed_services}",
                metadata={"results": {name: result.message for name, result in results}}
            )
        else:
            return OperationResult.success(
                "All indices ensured successfully",
                metadata={"results": {name: result.message for name, result in results}}
            )

    async def process_video(self, video_data: Dict[str, Any]) -> ProcessingResult:
        """Process a single video through all indexing services"""
        video_id = video_data.get("video_id", "unknown")
        
        # Store in MongoDB (critical operation)
        storage_result = await self.video_storage.store_video(video_data)
        
        # Index in Elasticsearch (non-critical)
        indexing_result = await self.search_indexing.index_video(video_data)
        
        # Update channel statistics (non-critical)
        stats_result = await self.channel_stats.update_channel_stats(video_data)
        
        result = ProcessingResult(
            video_id=video_id,
            storage_result=storage_result,
            indexing_result=indexing_result,
            stats_result=stats_result
        )
        
        if result.is_success:
            logger.debug(f"Successfully processed video: {video_id}")
        elif result.overall_status == OperationStatus.PARTIAL_SUCCESS:
            logger.warning(f"Partially processed video {video_id}: storage succeeded but other operations failed")
        else:
            logger.error(f"Failed to process video {video_id}: storage failed")
        
        return result

    async def _process_video_with_cleanup(self, video_data: Dict[str, Any]) -> ProcessingResult:
        """Process video and handle task cleanup"""
        task = asyncio.current_task()
        try:
            return await self.process_video(video_data)
        finally:
            # Clean up task reference
            if task:
                self._active_tasks.discard(task)

    async def run(self) -> None:
        """Main processing loop - consumes videos from queue and processes them"""
        logger.info("Starting VideoIndexingProcessor main loop")
        self._running = True
        
        try:
            while self._running and not self._shutdown_event.is_set():
                try:
                    # Check if we have capacity for more tasks
                    if len(self._active_tasks) >= self.max_concurrent_tasks:
                        # Wait for some tasks to complete
                        if self._active_tasks:
                            done, self._active_tasks = await asyncio.wait(
                                self._active_tasks, 
                                return_when=asyncio.FIRST_COMPLETED,
                                timeout=self.poll_interval
                            )
                        else:
                            await asyncio.sleep(self.poll_interval)
                        continue
                    
                    # Try to get video data from queue
                    video_data = await self._get_next_video()
                    
                    if video_data is None:
                        # No video available, wait before trying again
                        await asyncio.sleep(self.poll_interval)
                        continue
                    
                    # Create and track processing task
                    task = asyncio.create_task(
                        self._process_video_with_cleanup(video_data)
                    )
                    self._active_tasks.add(task)
                    
                    logger.debug(f"Started processing task for video: {video_data.get('video_id', 'unknown')}")
                    
                except asyncio.CancelledError:
                    logger.info("Processing loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in main processing loop: {e}")
                    await asyncio.sleep(self.poll_interval)
        
        finally:
            logger.info("Shutting down VideoIndexingProcessor")
            await self._cleanup_active_tasks()

    async def _get_next_video(self) -> Optional[Dict[str, Any]]:
        """Get next video from queue with timeout"""
        try:
            result =  self.input_queue.dequeue()
            return result
        except Exception as e:
            logger.error(f"Error getting video from queue: {e}")
            return None

    async def _cleanup_active_tasks(self) -> None:
        """Clean up any remaining active tasks"""
        if not self._active_tasks:
            return
        
        logger.info(f"Waiting for {len(self._active_tasks)} active tasks to complete")
        
        # Give tasks a chance to complete gracefully
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._active_tasks, return_exceptions=True),
                timeout=30.0  # 30 second timeout for graceful shutdown
            )
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for tasks to complete, cancelling remaining tasks")
            for task in self._active_tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for cancellations to complete
            await asyncio.gather(*self._active_tasks, return_exceptions=True)
        
        self._active_tasks.clear()

    async def stop(self) -> None:
        """Gracefully stop the processor"""
        logger.info("Stopping VideoIndexingProcessor")
        self._running = False
        self._shutdown_event.set()

    def is_running(self) -> bool:
        """Check if the processor is currently running"""
        return self._running

    @property
    def active_task_count(self) -> int:
        """Get the number of currently active processing tasks"""
        return len(self._active_tasks)

    async def health_check(self) -> HealthStatus:
        """Check health of all dependent services"""
        start_time = time.time()
        
        try:
            # Check all services concurrently
            health_checks = await asyncio.gather(
                self.video_storage.health_check(),
                self.search_indexing.health_check(),
                self.channel_stats.health_check(),
                return_exceptions=True
            )
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine overall health
            unhealthy_services = []
            service_statuses = {}
            
            for i, (service_name, check) in enumerate([
                ("storage", health_checks[0]),
                ("indexing", health_checks[1]), 
                ("stats", health_checks[2])
            ]):
                if isinstance(check, Exception):
                    unhealthy_services.append(service_name)
                    service_statuses[service_name] = f"Error: {str(check)}"
                elif not check.is_healthy:
                    unhealthy_services.append(service_name)
                    service_statuses[service_name] = check.message
                else:
                    service_statuses[service_name] = "healthy"
            
            is_healthy = len(unhealthy_services) == 0 and self._running
            processor_status = f"running ({self.active_task_count} active tasks)" if self._running else "stopped"
            message = f"Processor {processor_status}. " + ("All services healthy" if len(unhealthy_services) == 0 else f"Unhealthy services: {unhealthy_services}")
            
            return HealthStatus(
                service_name="video_processor",
                is_healthy=is_healthy,
                response_time_ms=response_time,
                message=message,
                metadata={
                    "services": service_statuses,
                    "active_tasks": self.active_task_count,
                    "is_running": self._running
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthStatus(
                service_name="video_processor",
                is_healthy=False,
                response_time_ms=response_time,
                message=f"Health check failed: {str(e)}"
            )