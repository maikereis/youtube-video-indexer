import traceback
from typing import Any, Dict

from ytindexer.config import settings
from ytindexer.database.elastic import ElasticConnection
from ytindexer.logging import logger


class SearchIndexingService:
    """Handles video search indexing in Elasticsearch"""
    
    def __init__(self, client = ElasticConnection()):
        self.client = client
        self.index_name = settings.search.index_name
        logger.info("Initialized SearchIndexingService")

    async def ensure_index(self):
        """Create Elasticsearch index if it doesn't exist"""
        if not await self.client.indices.exists(index=self.index_name):
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
            await self.client.indices.create(index=self.index_name, body=mapping)
            logger.info(f"Created Elasticsearch index: {self.index_name}")

    async def index_video(self, video_data: Dict[str, Any]) -> bool:
        """
        Index video metadata in Elasticsearch
        
        Returns True if successful, False otherwise
        """
        try:
            video_id = video_data.get("video_id")
            if not video_id:
                logger.warning("Video data missing video_id, skipping indexing")
                return False
            
            await self.client.index(
                index=self.index_name,
                id=video_id,
                body=video_data,
                refresh=True
            )
            
            logger.debug(f"Indexed video in Elasticsearch: {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index video in Elasticsearch: {str(e)}")
            logger.debug(traceback.format_exc())
            return False

    async def close(self):
        """Close the Elasticsearch client"""
        await self.client.close()