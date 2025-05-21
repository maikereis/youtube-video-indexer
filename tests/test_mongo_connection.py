import pytest
from unittest.mock import patch, MagicMock
from motor.motor_asyncio import AsyncIOMotorClient
from ytindexer.database import MongoConnection

def test_mongo_connection_singleton():
    with patch('ytindexer.database.mongo.AsyncIOMotorClient') as mock_client:
        # Create a mock instance to be returned by AsyncIOMotorClient
        mock_instance = MagicMock(spec=AsyncIOMotorClient)
        mock_client.return_value = mock_instance

        # Instantiate MongoConnection twice
        client1 = MongoConnection()
        client2 = MongoConnection()

        # Assert that AsyncIOMotorClient was called only once
        mock_client.assert_called_once()

        # Assert that both instances are the same (singleton behavior)
        assert client1 is client2