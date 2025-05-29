from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class VideoMetadata(BaseModel):
    """Video metadata response model"""
    video_id: str
    channel_id: Optional[str] = None
    title: Optional[str] = None
    published: Optional[datetime] = None
    updated: Optional[datetime] = None
    link: Optional[str] = None
    author: Optional[str] = None
    processed_at: Optional[datetime] = None
    indexed_at: Optional[datetime] = None
    source: str

class SearchResults(BaseModel):
    """Search results response model"""
    total: int
    results: List[VideoMetadata]
    page: int
    page_size: int
    page_count: int

class ChannelMetadata(BaseModel):
    """Channel metadata response model"""
    channel_id: str
    name: Optional[str] = None
    video_count: Optional[int] = None
    subscriber_count: Optional[int] = None
    first_seen: Optional[str] = None
    last_activity: Optional[str] = None

class ChannelResults(BaseModel):
    """Channel results response model"""
    total: int
    results: List[ChannelMetadata]
    page: int
    page_size: int
    page_count: int