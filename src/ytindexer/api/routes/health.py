from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    """API status endpoint"""
    return {
        "name": "YouTube Indexer API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs"
    }