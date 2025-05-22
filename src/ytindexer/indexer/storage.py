import traceback
from datetime import datetime
from typing import Any, Dict

from pymongo.errors import OperationFailure

from ytindexer.config import settings
from ytindexer.database.mongo import MongoConnection
from ytindexer.logging import logger

VIDEOS_COLLECTION_INDEXES = ("video_id", "channel_id", "published")

VIDEOS_COLLECTION = "videos"


class VideoStorageService:
    """Handles video metadata storage in MongoDB"""
    
    def __init__(self, client = MongoConnection()):
        self.client = client
        self.db = self.client[settings.mongo.name]
        self.videos_collection = self.db[VIDEOS_COLLECTION]
        logger.info("Initialized VideoStorageService")

    async def ensure_indices(self):
        """Ensure the required database indices exist"""
        for index in VIDEOS_COLLECTION_INDEXES:
            try:
                await self.videos_collection.create_index(index, unique=True)
                logger.debug(f"Created index: {index}")
            except OperationFailure:
                logger.debug(f"Index '{index}' already exists")

    async def store_video(self, video_data: Dict[str, Any]) -> bool:
        """
        Store video metadata in MongoDB
        
        Returns True if successful, False otherwise
        """
        try:
            video_id = video_data.get("video_id")
            if not video_id:
                logger.warning("Video data missing video_id, skipping")
                return False
            
            await self.videos_collection.update_one(
                {"video_id": video_id},
                {"$set": video_data},
                upsert=True
            )
            
            logger.debug(f"Stored video in MongoDB: {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store video in MongoDB: {str(e)}")
            logger.debug(traceback.format_exc())
            return False