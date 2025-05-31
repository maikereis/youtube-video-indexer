"""
Unit tests for the ElasticConnection class in ytindexer.database.elastic.

These tests verify:
- Successful connection to Elasticsearch with proper logging.
- Handling of connection errors with appropriate error logging.
- Connection reuse when already connected.
- Correct behavior of the close method, both when connected and when not connected.
- Thread-safety of concurrent connect calls (only one client instance created).
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from elasticsearch import ConnectionError

from ytindexer.database.elastic import ElasticConnection


@pytest.mark.asyncio
async def test_connect_success_logs_and_returns_client():
    """
    Test that ElasticConnection.connect() successfully establishes a connection,
    logs the success, and returns the Elasticsearch client.
    """
    dsn = "http://fake-elastic:9200"
    fake_client = AsyncMock()

    with patch(
        "ytindexer.database.elastic.AsyncElasticsearch", return_value=fake_client
    ) as mock_es, patch("ytindexer.database.elastic.logger") as mock_logger:
        conn = ElasticConnection(dsn)
        client = await conn.connect()

        assert client == fake_client
        mock_es.assert_called_once_with(dsn)
        mock_logger.info.assert_called_once_with(
            "Successfully connected to Elastic at: {host}", host=dsn
        )


@pytest.mark.asyncio
async def test_connect_raises_connection_error_and_logs():
    """
    Test that ElasticConnection.connect() raises ConnectionError when the connection fails,
    and logs an appropriate error message.
    """
    dsn = "http://fake-elastic:9200"
    with patch(
        "ytindexer.database.elastic.AsyncElasticsearch",
        side_effect=ConnectionError("fail"),
    ) as mock_es, patch("ytindexer.database.elastic.logger") as mock_logger:
        conn = ElasticConnection(dsn)

        with pytest.raises(ConnectionError):
            await conn.connect()

        mock_es.assert_called_once_with(dsn)
        mock_logger.error.assert_called_once()
        error_msg = mock_logger.error.call_args[0][0]
        assert "Couldn't connect to Elastic" in error_msg


@pytest.mark.asyncio
async def test_connect_returns_existing_client_if_already_connected():
    """
    Test that ElasticConnection.connect() returns the existing client instance if already connected,
    avoiding redundant connections.
    """
    dsn = "http://fake-elastic:9200"
    fake_client = AsyncMock()

    with patch(
        "ytindexer.database.elastic.AsyncElasticsearch", return_value=fake_client
    ):
        conn = ElasticConnection(dsn)
        client1 = await conn.connect()
        client2 = await conn.connect()

        assert client1 is client2  # Should be the same instance


@pytest.mark.asyncio
async def test_close_calls_client_close_and_resets_client():
    """
    Test that ElasticConnection.close() calls the client's close method
    and resets the internal _client attribute to None.
    """
    dsn = "http://fake-elastic:9200"
    fake_client = AsyncMock()

    with patch(
        "ytindexer.database.elastic.AsyncElasticsearch", return_value=fake_client
    ):
        conn = ElasticConnection(dsn)
        await conn.connect()

        await conn.close()

        fake_client.close.assert_awaited_once()
        assert conn._client is None


@pytest.mark.asyncio
async def test_close_without_connect_does_nothing():
    """
    Test that calling ElasticConnection.close() without an active connection
    does not raise any errors and leaves _client as None.
    """
    dsn = "http://fake-elastic:9200"
    conn = ElasticConnection(dsn)

    await conn.close()

    assert conn._client is None


@pytest.mark.asyncio
async def test_concurrent_connect_calls_create_single_client():
    """
    Test that concurrent calls to ElasticConnection.connect() result in
    only one client being created, ensuring thread-safety.
    """
    dsn = "http://localhost:9200"
    fake_client = AsyncMock()

    with patch(
        "ytindexer.database.elastic.AsyncElasticsearch", return_value=fake_client
    ) as mock_elastic:
        conn = ElasticConnection(dsn)
        connect_calls = [conn.connect() for _ in range(10)]
        results = await asyncio.gather(*connect_calls)

        for client in results:
            assert client is fake_client

        mock_elastic.assert_called_once_with(dsn)
