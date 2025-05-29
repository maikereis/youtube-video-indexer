from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


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