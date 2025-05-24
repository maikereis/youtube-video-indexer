import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import valkey
from valkey.exceptions import ConnectionError
from ytindexer.database.valkey import ValkeyConnection  # adjust import as needed


@pytest.mark.asyncio
async def test_connect_success_logs_and_returns_client():
    host = "valkey_host"
    port = 1234
    password = "secret"

    fake_client = MagicMock()
    fake_client.ping = MagicMock()

    with patch("ytindexer.database.valkey.valkey.Valkey", return_value=fake_client) as mock_valkey, \
         patch("ytindexer.database.valkey.logger") as mock_logger:
        conn = ValkeyConnection(host, port, password)
        client = await conn.connect()

        assert client == fake_client
        mock_valkey.assert_called_once_with(
            host=host, port=port, username=None, password=password, db=0
        )
        fake_client.ping.assert_called_once()
        mock_logger.info.assert_called_once_with("Successfully connected to Valkey at: {host}", host=host)

@pytest.mark.asyncio
async def test_connect_raises_connection_error_and_logs():
    host = "valkey_host"
    port = 1234
    password = "secret"

    with patch("ytindexer.database.valkey.valkey.Valkey") as mock_valkey, \
         patch("ytindexer.database.valkey.logger") as mock_logger:
        # Setup the Valkey constructor to raise a ConnectionError on instantiation
        mock_valkey.side_effect = ConnectionError("fail")

        conn = ValkeyConnection(host, port, password)

        with pytest.raises(ConnectionError):
            await conn.connect()

        mock_valkey.assert_called_once_with(
            host=host, port=port, username=None, password=password, db=0
        )
        mock_logger.error.assert_called_once()
        err_msg = mock_logger.error.call_args[0][0]
        assert "Couldn't connect to the Valkey" in err_msg

@pytest.mark.asyncio
async def test_connect_returns_existing_client_if_already_connected():
    host = "valkey_host"
    port = 1234
    password = "secret"

    fake_client = MagicMock()
    fake_client.ping = MagicMock()

    with patch("ytindexer.database.valkey.valkey.Valkey", return_value=fake_client):
        conn = ValkeyConnection(host, port, password)
        client1 = await conn.connect()
        client2 = await conn.connect()

        assert client1 is client2

@pytest.mark.asyncio
async def test_close_calls_close_and_resets_client():
    host = "valkey_host"
    port = 1234
    password = "secret"

    fake_client = MagicMock()
    fake_client.aclose = MagicMock()

    with patch("ytindexer.database.valkey.valkey.Valkey", return_value=fake_client):
        conn = ValkeyConnection(host, port, password)
        await conn.connect()

        await conn.close()

        fake_client.close.assert_called_once()
        assert conn._client is None

@pytest.mark.asyncio
async def test_close_without_connect_does_nothing():
    host = "valkey_host"
    port = 1234
    password = "secret"

    conn = ValkeyConnection(host, port, password)

    # _client is None, close should not raise and keep _client None
    await conn.close()
    assert conn._client is None


@pytest.mark.asyncio
async def test_concurrent_connect_calls_create_single_client():
    host = "localhost"
    port = 1234
    password = "secret"

    fake_client = MagicMock()
    fake_client.ping.return_value = None
    fake_client.close = MagicMock()

    with patch("ytindexer.database.valkey.valkey.Valkey", return_value=fake_client) as mock_valkey:
        conn = ValkeyConnection(host, port, password)

        # Create multiple concurrent connect calls
        connect_calls = [conn.connect() for _ in range(10)]

        # Run concurrently
        results = await asyncio.gather(*connect_calls)

        # All results should be the same client instance
        for client in results:
            assert client is fake_client

        # Valkey constructor called once with the right args
        mock_valkey.assert_called_once_with(
            host=host,
            port=port,
            username=None,
            password=password,
            db=0,
        )

        # ping method called once
        fake_client.ping.assert_called_once()


@pytest.mark.asyncio
async def test_close_calls_close_and_clears_client():
    host = "localhost"
    port = 1234
    password = "secret"

    fake_client = MagicMock()
    fake_client.ping.return_value = None
    fake_client.close = MagicMock()

    with patch("ytindexer.database.valkey.valkey.Valkey", return_value=fake_client):
        conn = ValkeyConnection(host, port, password)

        # connect to set _client
        await conn.connect()

        # call close, should call aclose and set _client to None
        await conn.close()

        fake_client.close.assert_called_once()
        assert conn._client is None