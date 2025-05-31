"""
Unit tests for the AsyncDatabaseConnection abstract base class and its
minimal concrete implementation DummyConnection.

This module tests:
- That unimplemented abstract methods raise NotImplementedError.
- That the concrete DummyConnection correctly implements connect and close methods.
- That DummyConnection initialization sets attributes correctly.
"""

import asyncio
import pytest
from ytindexer.database import AsyncDatabaseConnection


class DummyConnection(AsyncDatabaseConnection[str]):
    """
    Minimal concrete implementation of AsyncDatabaseConnection for testing.

    Attributes:
        name (str): Identifier for the connection instance.
        connected (bool): Flag indicating whether the connection is active.
        closed (bool): Flag indicating whether the connection has been closed.
    """

    def __init__(self, name: str):
        """
        Initialize the DummyConnection instance.

        Args:
            name (str): Name or identifier for the connection instance.
        """
        self.name = name
        self.connected = False
        self.closed = False

    async def connect(self) -> str:
        """
        Simulate an asynchronous connection establishment.

        Returns:
            str: A string indicating successful connection with the name.
        """
        await asyncio.sleep(0.01)
        self.connected = True
        return f"Connected-{self.name}"

    async def close(self) -> None:
        """
        Simulate an asynchronous closing of the connection.

        Returns:
            None
        """
        await asyncio.sleep(0.01)
        self.closed = True


@pytest.mark.asyncio
async def test_abstract_methods_raise():
    """
    Test that calling abstract methods without implementation raises NotImplementedError.
    """

    class TempConnection(AsyncDatabaseConnection):
        async def connect(self):
            raise NotImplementedError

        async def close(self):
            raise NotImplementedError

    conn = TempConnection()
    with pytest.raises(NotImplementedError):
        await conn.connect()

    with pytest.raises(NotImplementedError):
        await conn.close()


@pytest.mark.asyncio
async def test_concrete_connect_returns_expected():
    """
    Test that DummyConnection.connect() returns the expected string and updates the connected flag.
    """
    conn = DummyConnection("testdb")
    result = await conn.connect()
    assert result == "Connected-testdb"
    assert conn.connected is True


@pytest.mark.asyncio
async def test_concrete_close_marks_closed():
    """
    Test that DummyConnection.close() sets the closed flag to True after being called.
    """
    conn = DummyConnection("testdb")
    await conn.connect()
    await conn.close()
    assert conn.closed is True


def test_init_accepts_parameters():
    """
    Test that DummyConnection.__init__ correctly assigns attributes.
    """
    conn = DummyConnection("param_test")
    assert conn.name == "param_test"
    assert not conn.connected
    assert not conn.closed
