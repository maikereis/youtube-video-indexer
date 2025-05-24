import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pymongo.errors import ConnectionFailure

from ytindexer.database.mongo import MongoConnection  # Adjust import as needed


@pytest.mark.asyncio
async def test_connect_success_logs_and_returns_client():
    dsn = "mongodb://fake-mongo:27017"
    fake_client = AsyncMock()
    fake_admin_db = AsyncMock()
    fake_client.admin = fake_admin_db
    fake_admin_db.command = AsyncMock(return_value={"ok": 1})

    with patch("ytindexer.database.mongo.AsyncIOMotorClient", return_value=fake_client) as mock_motor, \
         patch("ytindexer.database.mongo.logger") as mock_logger:
        conn = MongoConnection(dsn)
        client = await conn.connect()

        assert client == fake_client
        mock_motor.assert_called_once_with(dsn)
        fake_admin_db.command.assert_awaited_once_with("ping")
        mock_logger.info.assert_called_once_with("Successfully connected to MongoDB at: {host}", host=dsn)

@pytest.mark.asyncio
async def test_connect_raises_connection_failure_and_logs():
    dsn = "mongodb://fake-mongo:27017"

    with patch("ytindexer.database.mongo.AsyncIOMotorClient") as mock_motor, \
         patch("ytindexer.database.mongo.logger") as mock_logger:
        # Setup the client to raise ConnectionFailure on ping
        instance = MagicMock()
        instance.admin.command = AsyncMock(side_effect=ConnectionFailure("fail"))
        mock_motor.return_value = instance

        conn = MongoConnection(dsn)

        with pytest.raises(ConnectionFailure):
            await conn.connect()

        mock_motor.assert_called_once_with(dsn)
        instance.admin.command.assert_awaited_once_with("ping")
        mock_logger.error.assert_called_once()
        error_msg = mock_logger.error.call_args[0][0]
        assert "Couldn't connect to the MongoDB database" in error_msg

@pytest.mark.asyncio
async def test_connect_returns_existing_client_if_already_connected():
    dsn = "mongodb://fake-mongo:27017"
    fake_client = AsyncMock()
    fake_admin_db = AsyncMock()
    fake_client.admin = fake_admin_db
    fake_admin_db.command = AsyncMock(return_value={"ok": 1})

    with patch("ytindexer.database.mongo.AsyncIOMotorClient", return_value=fake_client):
        conn = MongoConnection(dsn)
        client1 = await conn.connect()
        client2 = await conn.connect()
        assert client1 is client2  # Same instance returned

@pytest.mark.asyncio
async def test_close_calls_client_close_and_resets_client():
    dsn = "mongodb://fake-mongo:27017"
    fake_client = AsyncMock()
    fake_client.close = MagicMock()

    with patch("ytindexer.database.mongo.AsyncIOMotorClient", return_value=fake_client):
        conn = MongoConnection(dsn)
        await conn.connect()

        await conn.close()

        fake_client.close.assert_called_once()
        assert conn._client is None

@pytest.mark.asyncio
async def test_close_without_connect_does_nothing():
    dsn = "mongodb://fake-mongo:27017"
    conn = MongoConnection(dsn)
    # _client is None, close should do nothing and not raise
    await conn.close()
    assert conn._client is None

@pytest.mark.asyncio
async def test_concurrent_connect_calls_create_single_client():
    dsn = "mongodb://localhost:27017"

    # Mock AsyncIOMotorClient instance and its admin.command coroutine
    fake_client = AsyncMock()
    fake_client.admin.command = AsyncMock(return_value={"ok": 1})

    # Patch AsyncIOMotorClient to return the fake_client
    with patch("ytindexer.database.mongo.AsyncIOMotorClient", return_value=fake_client) as mock_motor:
        conn = MongoConnection(dsn)

        # Create multiple concurrent connect calls
        connect_calls = [conn.connect() for _ in range(10)]

        # Run all connect calls concurrently
        results = await asyncio.gather(*connect_calls)

        # Assert all returned clients are the same instance
        for client in results:
            assert client is fake_client

        # Assert AsyncIOMotorClient constructor called exactly once
        mock_motor.assert_called_once_with(dsn)

        # Assert ping (admin.command('ping')) called exactly once
        fake_client.admin.command.assert_awaited_once_with('ping')
