from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ytindexer.api.dependencies import get_limiter, get_mongo_connection
from ytindexer.api.models.response import ChannelMetadata, ChannelResults
from ytindexer.config import settings
from ytindexer.indexer.config import MongoDBConfig
from ytindexer.logging import logger

router = APIRouter()
limiter = get_limiter()


@router.get("", response_model=ChannelResults)
@limiter.limit("30/minute")
async def list_channels(
    request: Request,
    q: Optional[str] = None,
    sort: str = "last_activity:desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    mongo_conn: Any = Depends(get_mongo_connection),
):
    """
    List indexed channels

    - **q**: Optional search query for channel name
    - **sort**: Sort order (last_activity:desc, video_count:desc, etc.)
    - **page**: Page number
    - **page_size**: Number of results per page
    """
    try:
        # Build MongoDB query
        query = {}
        if q:
            query["name"] = {"$regex": q, "$options": "i"}

        # Parse sort parameter
        sort_field, sort_order = sort.split(":")
        sort_param = [(sort_field, 1 if sort_order == "asc" else -1)]

        # Calculate pagination
        skip = (page - 1) * page_size

        db = mongo_conn[settings.mongo.name]
        collection = db[MongoDBConfig.videos_collection]

        # Get total count
        total_count = await collection.count_documents(query)

        # Execute query
        cursor = collection.find(query)
        cursor = cursor.sort(sort_param)
        cursor = cursor.skip(skip).limit(page_size)

        # Extract results
        channels = []
        async for doc in cursor:
            # Remove MongoDB _id field
            if "_id" in doc:
                del doc["_id"]
            channels.append(ChannelMetadata(**doc))

        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size

        return ChannelResults(
            total=total_count,
            results=channels,
            page=page,
            page_size=page_size,
            page_count=total_pages,
        )

    except Exception as e:
        logger.error(f"Error listing channels: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
