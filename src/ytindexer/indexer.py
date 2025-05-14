import asyncio
import json
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from ytindexer.logging import logger
from ytindexer.queue import Queue
from ytindexer.config import settings

import motor.motor_asyncio
from elasticsearch import AsyncElasticsearch
from pymongo.errors import OperationFailure

VIDEOS_COLLECTION_INDEXES = ("video_id", "channel_id", "published",)
CHANNELS_COLLECTION_INDEXES = ("channel_id",)

class VideoIndexer:
    """
    Indexes processed YouTube video metadata into database and search engine
    """
    def __init__(self, input_queue: Queue):
        self.input_queue = input_queue
        # Setup MongoDB connection
        self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongo.dsn)
        self.db = self.mongo_client[settings.mongo.name]

        self.videos_collection = self.db["videos"]
        self.channels_collection = self.db["channels"]

        self.es_client = AsyncElasticsearch(settings.search.dsn)
        self.index_name = settings.search.index_name

        logger.info("Initialized VideoIndexer")

    async def ensure_indices(self):
        """Ensure the required database indices and mappings exist"""
        # Create MongoDB indices

        for index in VIDEOS_COLLECTION_INDEXES:
            try:
                await self.videos_collection.create_index(index, unique=True)
            except OperationFailure as opf:
                logger.warning(f"Index '{index}' already created")

        for index in CHANNELS_COLLECTION_INDEXES:
            try:
                await self.channels_collection.create_index(index, unique=True)
            except OperationFailure as opf:
                logger.warning(f"Index '{index}' already created")

        
        # Create Elasticsearch index if it doesn't exist
        if not await self.es_client.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "video_id": {"type": "keyword"},
                        "channel_id": {"type": "keyword"},
                        "title": {
                            "type": "text",
                            "analyzer": "standard",
                            "fields": {
                                "keyword": {"type": "keyword", "ignore_above": 256}
                            }
                        },
                        "description": {"type": "text", "analyzer": "standard"},
                        "published": {"type": "date"},
                        "updated": {"type": "date"},
                        "author": {
                            "type": "text",
                            "fields": {
                                "keyword": {"type": "keyword", "ignore_above": 256}
                            }
                        },
                        "tags": {"type": "keyword"},
                        "categories": {"type": "keyword"},
                        "duration": {"type": "integer"},
                        "view_count": {"type": "long"},
                        "like_count": {"type": "long"},
                        "comment_count": {"type": "long"},
                        "processed_at": {"type": "date"}
                    }
                },
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                }
            }
            await self.es_client.indices.create(index=self.index_name, body=mapping)
            logger.info(f"Created Elasticsearch index: {self.index_name}")

    async def store_video(self, video_data: Dict[str, Any]) -> bool:
        """
        Store video metadata in MongoDB and index in Elasticsearch
        
        Returns True if successful, False otherwise
        """
        try:
            video_id = video_data.get("video_id")
            if not video_id:
                logger.warning("Video data missing video_id, skipping")
                return False
            
            # Store in MongoDB (upsert to handle updates)
            await self.videos_collection.update_one(
                {"video_id": video_id},
                {"$set": video_data},
                upsert=True
            )
            
            # Index in Elasticsearch
            await self.es_client.index(
                index=self.index_name,
                id=video_id,
                body=video_data,
                refresh=True
            )
            
            logger.debug(f"Indexed video: {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store video: {str(e)}")
            logger.debug(traceback.format_exc())
            return False
            
    async def update_channel_stats(self, video_data: Dict[str, Any]):
        """Update channel statistics based on video data"""
        channel_id = video_data.get("channel_id")
        if not channel_id:
            return
            
        # Update channel document with video count and last activity
        await self.channels_collection.update_one(
            {"channel_id": channel_id},
            {
                "$inc": {"video_count": 1},
                "$set": {"last_activity": datetime.utcnow().isoformat()},
                "$setOnInsert": {"first_seen": datetime.utcnow().isoformat()}
            },
            upsert=True
        )
    
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
            success = await self.store_video(item)
            if success:
                await self.update_channel_stats(item)
                processed += 1
                
        logger.info(f"Indexed {processed}/{len(items)} videos")
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
            await self.es_client.close()
