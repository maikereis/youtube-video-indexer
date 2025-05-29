import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from elasticsearch import ConnectionError

from ytindexer.database.elastic import \
    ElasticConnection  # adjust import path as needed


@pytest.mark.asyncio
async def test_connect_success_logs_and_returns_client():
    dsn = "http://fake-elastic:9200"
    fake_client = AsyncMock()

    with patch("ytindexer.database.elastic.AsyncElasticsearch", return_value=fake_client) as mock_es, \
         patch("ytindexer.database.elastic.logger") as mock_logger:
        conn = ElasticConnection(dsn)
        client = await conn.connect()

        assert client == fake_client
        mock_es.assert_called_once_with(dsn)
        mock_logger.info.assert_called_once_with("Successfully connected to Elastic at: {host}", host=dsn)

@pytest.mark.asyncio
async def test_connect_raises_connection_error_and_logs():
    dsn = "http://fake-elastic:9200"
    with patch("ytindexer.database.elastic.AsyncElasticsearch", side_effect=ConnectionError("fail")) as mock_es, \
         patch("ytindexer.database.elastic.logger") as mock_logger:
        conn = ElasticConnection(dsn)

        with pytest.raises(ConnectionError):
            await conn.connect()

        mock_es.assert_called_once_with(dsn)
        mock_logger.error.assert_called_once()
        error_msg = mock_logger.error.call_args[0][0]
        assert "Couldn't connect to Elastic" in error_msg

@pytest.mark.asyncio
async def test_connect_returns_existing_client_if_already_connected():
    dsn = "http://fake-elastic:9200"
    fake_client = AsyncMock()

    with patch("ytindexer.database.elastic.AsyncElasticsearch", return_value=fake_client):
        conn = ElasticConnection(dsn)
        client1 = await conn.connect()
        client2 = await conn.connect()
        assert client1 is client2  # Same instance returned

@pytest.mark.asyncio
async def test_close_calls_client_close_and_resets_client():
    dsn = "http://fake-elastic:9200"
    fake_client = AsyncMock()

    with patch("ytindexer.database.elastic.AsyncElasticsearch", return_value=fake_client):
        conn = ElasticConnection(dsn)
        await conn.connect()

        await conn.close()

        fake_client.close.assert_awaited_once()
        assert conn._client is None

@pytest.mark.asyncio
async def test_close_without_connect_does_nothing():
    dsn = "http://fake-elastic:9200"
    conn = ElasticConnection(dsn)
    # _client is None, close should do nothing and not error
    await conn.close()
    assert conn._client is None



@pytest.mark.asyncio
async def test_concurrent_connect_calls_create_single_client():
    dsn = "http://localhost:9200"

    fake_client = AsyncMock()

    with patch("ytindexer.database.elastic.AsyncElasticsearch", return_value=fake_client) as mock_elastic:
        conn = ElasticConnection(dsn)
        connect_calls = [conn.connect() for _ in range(10)]
        results = await asyncio.gather(*connect_calls)

        for client in results:
            assert client is fake_client

        mock_elastic.assert_called_once_with(dsn)