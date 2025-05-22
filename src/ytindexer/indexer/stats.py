import traceback
from datetime import datetime
from typing import Any, Dict

from pymongo.errors import OperationFailure

from ytindexer.config import settings
from ytindexer.database.mongo import MongoConnection
from ytindexer.logging import logger

CHANNELS_COLLECTION_INDEXES = ("channel_id",)

CHANNELS_COLLECTION = "channels"

class ChannelStatsService:
    """Handles channel statistics updates"""
    
    def __init__(self, client = MongoConnection()):
        self.client = client
        self.db = self.client[settings.mongo.name]
        self.channels_collection = self.db[CHANNELS_COLLECTION]
        logger.info("Initialized ChannelStatsService")

    async def ensure_indices(self):
        """Ensure the required database indices exist"""
        for index in CHANNELS_COLLECTION_INDEXES:
            try:
                await self.channels_collection.create_index(index, unique=True)
                logger.debug(f"Created index: {index}")
            except OperationFailure:
                logger.debug(f"Index '{index}' already exists")

    async def update_channel_stats(self, video_data: Dict[str, Any]) -> bool:
        """Update channel statistics based on video data"""
        try:
            channel_id = video_data.get("channel_id")
            if not channel_id:
                logger.warning("Video data missing channel_id, skipping stats update")
                return False
                
            await self.channels_collection.update_one(
                {"channel_id": channel_id},
                {
                    "$inc": {"video_count": 1},
                    "$set": {"last_activity": datetime.utcnow().isoformat()},
                    "$setOnInsert": {"first_seen": datetime.utcnow().isoformat()}
                },
                upsert=True
            )
            
            logger.debug(f"Updated channel stats: {channel_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update channel stats: {str(e)}")
            logger.debug(traceback.format_exc())
            return False