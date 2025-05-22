    import asyncio
    import traceback
    from typing import Any, Dict, List

    from ytindexer.indexer.indexing import SearchIndexingService
    from ytindexer.indexer.stats import ChannelStatsService
    from ytindexer.indexer.storage import VideoStorageService
    from ytindexer.logging import logger
    from ytindexer.queues import Queue


    class VideoIndexer:
        """
        Orchestrates the video indexing process by coordinating different services
        """
        
        def __init__(self, input_queue: Queue, video_storage=VideoStorageService(), search_indexing=SearchIndexingService(), channel_stats=ChannelStatsService()):
            self.input_queue = input_queue
            self.video_storage = video_storage
            self.search_indexing = search_indexing
            self.channel_stats = channel_stats
            logger.info("Initialized VideoIndexer")

        async def ensure_indices(self):
            """Ensure all required database indices and mappings exist"""
            await self.video_storage.ensure_indices()
            await self.search_indexing.ensure_index()
            await self.channel_stats.ensure_indices()

        async def process_video(self, video_data: Dict[str, Any]) -> bool:
            """
            Process a single video through all indexing services
            
            Returns True if all operations succeeded, False otherwise
            """
            video_id = video_data.get("video_id", "unknown")
            
            # Store in MongoDB
            storage_success = await self.video_storage.store_video(video_data)
            if not storage_success:
                logger.error(f"Failed to store video {video_id} in MongoDB")
                return False
            
            # Index in Elasticsearch
            indexing_success = await self.search_indexing.index_video(video_data)
            if not indexing_success:
                logger.error(f"Failed to index video {video_id} in Elasticsearch")
                # Continue processing even if search indexing fails
            
            # Update channel statistics
            stats_success = await self.channel_stats.update_channel_stats(video_data)
            if not stats_success:
                logger.error(f"Failed to update channel stats for video {video_id}")
                # Continue processing even if stats update fails
            
            # Consider successful if storage succeeded (minimum requirement)
            success = storage_success
            if success:
                logger.debug(f"Successfully processed video: {video_id}")
            
            return success

        async def process_batch(self, batch_size: int = 10) -> int:
            """
            Process a batch of video metadata entries from the queue
            
            Returns the number of successfully processed entries
            """
            items = self.input_queue.batch_dequeue(batch_size)
            if not items:
                return 0
                
            processed = 0
            for item in items:
                success = await self.process_video(item)
                if success:
                    processed += 1
                    
            logger.info(f"Processed {processed}/{len(items)} videos")
            return processed
            
        async def run_worker(self, poll_interval: float = 0.5):
            """
            Run the indexer worker process to continuously process video metadata
            """
            logger.info("Starting video indexer worker")
            
            try:
                await self.ensure_indices()
                
                while True:
                    queue_size = self.input_queue.queue_size()
                    
                    if queue_size > 0:
                        logger.debug(f"Queue has {queue_size} items pending")
                        await self.process_batch()
                    else:
                        # If queue is empty, sleep before checking again
                        await asyncio.sleep(poll_interval)
                        
            except KeyboardInterrupt:
                logger.info("Indexer shutting down gracefully")
            except Exception as e:
                logger.error(f"Indexer encountered an error: {str(e)}")
                logger.error(traceback.format_exc())
            finally:
                await self.search_indexing.close()