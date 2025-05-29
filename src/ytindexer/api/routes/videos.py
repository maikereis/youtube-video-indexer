from typing import Optional, Any

from fastapi import APIRouter, Request, Depends, HTTPException, Query

from ytindexer.api.dependencies import get_limiter, get_elastic_connection
from ytindexer.api.models.response import SearchResults, VideoMetadata

from ytindexer.config import settings

from ytindexer.logging import configure_logging, logger

configure_logging(log_level="INFO", log_file="logs/videos.log")

router = APIRouter()
limiter = get_limiter()

# API routes for video data
@router.get("", response_model=SearchResults)
@limiter.limit("30/minute")
async def search_videos(
    request: Request,
    q: Optional[str] = None,
    channel_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    sort: str = "published:desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    es_conn: Any = Depends(get_elastic_connection)
):
    """
    Search for videos with various filters
    
    - **q**: Optional search query for video title/description
    - **channel_id**: Optional filter by channel ID
    - **from_date**: Optional start date filter (ISO format)
    - **to_date**: Optional end date filter (ISO format)
    - **sort**: Sort order (published:desc, published:asc, etc.)
    - **page**: Page number
    - **page_size**: Number of results per page
    """
    try:
        # Build Elasticsearch query
        es_query = {"bool": {"must": []}}

        # Add text search if provided
        if q:
            es_query["bool"]["must"].append(
                {
                    "multi_match": {
                        "query": q,
                        "fields": ["title^3", "description", "tags^2"],
                    }
                }
            )

        # Add channel filter if provided
        if channel_id:
            es_query["bool"]["must"].append({"term": {"channel_id": channel_id}})

        # Add date range if provided
        if from_date or to_date:
            date_range = {}
            if from_date:
                date_range["gte"] = from_date
            if to_date:
                date_range["lte"] = to_date

            es_query["bool"]["must"].append({"range": {"published": date_range}})

        # Parse sort parameter
        if sort:
            sort_field, sort_order = sort.split(":")
            sort_param = [{sort_field: sort_order}]
        else:
            sort_param = [{"published": "desc"}]  # Default sorting

        # Ensure page starts at 1 or higher
        page = max(1, page)
        from_index = (page - 1) * page_size

        # Execute search query
        search_results = await es_conn.search(
            index=settings.search.index_name,
            query=es_query,
            sort=sort_param,
            from_=from_index,
            size=page_size,
        )

        # Extract results
        total_hits = search_results["hits"]["total"]["value"]
        videos = []

        for hit in search_results["hits"]["hits"]:
            video_data = hit["_source"]
            videos.append(VideoMetadata(**video_data))

        # Calculate total pages
        total_pages = (total_hits + page_size - 1) // page_size

        return SearchResults(
            total=total_hits,
            results=videos,
            page=page,
            page_size=page_size,
            page_count=total_pages,
        )

    except Exception as e:
        logger.error(f"Error searching videos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))