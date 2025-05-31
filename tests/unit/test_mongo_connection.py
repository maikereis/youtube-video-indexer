"""
Unit tests for the MongoConnection class in ytindexer.database.mongo.

Tests cover:
- Successful connection to MongoDB, including logging behavior.
- Handling and logging of connection failures.
- Ensuring a single client instance is reused across multiple connect calls.
- Proper closing of the client connection and resetting state.
- Handling close calls without prior connection.
- Concurrent connection calls to verify single client creation and connection.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pymongo.errors import ConnectionFailure

from ytindexer.database.mongo import MongoConnection


@pytest.mark.asyncio
async def test_connect_success_logs_and_returns_client():
    """
    Test that MongoConnection.connect:
    - Creates a client using AsyncIOMotorClient.
    - Successfully pings the database via admin.command("ping").
    - Returns the client instance.
    - Logs a success info message.
    """
    dsn = "mongodb://fake-mongo:27017"
    fake_client = AsyncMock()
    fake_admin_db = AsyncMock()
    fake_client.admin = fake_admin_db
    fake_admin_db.command = AsyncMock(return_value={"ok": 1})

    with patch(
        "ytindexer.database.mongo.AsyncIOMotorClient", return_value=fake_client
    ) as mock_motor, patch("ytindexer.database.mongo.logger") as mock_logger:
        conn = MongoConnection(dsn)
        client = await conn.connect()

        assert client == fake_client
        mock_motor.assert_called_once_with(dsn)
        fake_admin_db.command.assert_awaited_once_with("ping")
        mock_logger.info.assert_called_once_with(
            "Successfully connected to MongoDB at: {host}", host=dsn
        )


@pytest.mark.asyncio
async def test_connect_raises_connection_failure_and_logs():
    """
    Test that MongoConnection.connect:
    - Raises ConnectionFailure if the ping command fails.
    - Logs an error message upon failure.
    """
    dsn = "mongodb://fake-mongo:27017"

    with patch("ytindexer.database.mongo.AsyncIOMotorClient") as mock_motor, patch(
        "ytindexer.database.mongo.logger"
    ) as mock_logger:
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
    """
    Test that MongoConnection.connect:
    - Returns the existing client instance if already connected.
    - Does not create a new client or ping the database again.
    """
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
    """
    Test that MongoConnection.close:
    - Calls the client's close method.
    - Resets the internal _client attribute to None.
    """
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
    """
    Test that MongoConnection.close:
    - Does not fail or throw if called without a prior connection.
    - Leaves the internal _client attribute as None.
    """
    dsn = "mongodb://fake-mongo:27017"
    conn = MongoConnection(dsn)
    await conn.close()
    assert conn._client is None


@pytest.mark.asyncio
async def test_concurrent_connect_calls_create_single_client():
    """
    Test that multiple concurrent calls to MongoConnection.connect:
    - Only create one AsyncIOMotorClient instance.
    - Only ping the database once.
    - Return the same client instance to all callers.
    """
    dsn = "mongodb://localhost:27017"

    fake_client = AsyncMock()
    fake_client.admin.command = AsyncMock(return_value={"ok": 1})

    with patch(
        "ytindexer.database.mongo.AsyncIOMotorClient", return_value=fake_client
    ) as mock_motor:
        conn = MongoConnection(dsn)

        connect_calls = [conn.connect() for _ in range(10)]
        results = await asyncio.gather(*connect_calls)

        for client in results:
            assert client is fake_client

        mock_motor.assert_called_once_with(dsn)
        fake_client.admin.command.assert_awaited_once_with("ping")
