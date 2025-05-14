import os

import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()  # Load variables from .env

@pytest.mark.asyncio
async def test_mongodb_connection():
    host = os.getenv("MONGO_HOST", "localhost")
    port = os.getenv("MONGO_PORT", "27017")
    uri = f"mongodb://{host}:{port}"
    
    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)

    try:
        response = await client.admin.command('ping')
        assert response['ok'] == 1.0  # Check that ping succeeded
    except Exception as e:
        pytest.fail(f"Could not connect to MongoDB: {e}")
