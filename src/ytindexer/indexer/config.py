import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ElasticsearchConfig:
    """Configuration for Elasticsearch indexing"""

    index_name: str = 'videos'
    shards: int = 1
    replicas: int = 0

    @property
    def mapping(self) -> Dict[str, Any]:
        return {
            "mappings": {
                "properties": {
                    "video_id": {"type": "keyword"},
                    "channel_id": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                    },
                    "description": {"type": "text", "analyzer": "standard"},
                    "published": {"type": "date"},
                    "updated": {"type": "date"},
                    "author": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                    },
                    "tags": {"type": "keyword"},
                    "categories": {"type": "keyword"},
                    "duration": {"type": "integer"},
                    "view_count": {"type": "long"},
                    "like_count": {"type": "long"},
                    "comment_count": {"type": "long"},
                    "processed_at": {"type": "date"},
                }
            },
            "settings": {
                "number_of_shards": self.shards,
                "number_of_replicas": self.replicas,
            },
        }


@dataclass
class MongoDBConfig:
    """Configuration for MongoDB collections and indexes"""

    database_name: str = 'mongo'
    videos_collection: str = "videos"
    channels_collection: str = "channels"

    @property
    def video_indexes(self) -> Dict[str, Dict[str, Any]]:
        return {
            "video_id": {
                "key": [("video_id", 1)],
                "unique": True,
                "name": "video_id_idx",
            },
            "channel_id_non": {
                "key": [("channel_id", 1)],
                "unique": False,
                "name": "channel_id_non_idx",
            },
            "published_non": {
                "key": [("published", 1)],
                "unique": False,
                "name": "published_non_idx",
            },
        }

    @property
    def channel_indexes(self) -> Dict[str, Dict[str, Any]]:
        return {
            "channel_id": {
                "key": [("channel_id", 1)],
                "unique": True,
                "name": "channel_id_idx",
            }
        }


@dataclass
class RetryConfig:
    """Configuration for retry logic"""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
