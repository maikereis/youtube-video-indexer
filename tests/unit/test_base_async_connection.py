import pytest
import asyncio
from ytindexer.database import AsyncDatabaseConnection  # adjust if it's in a submodule, e.g. ytindexer.db.base

# Minimal concrete subclass for testing
class DummyConnection(AsyncDatabaseConnection[str]):
    def __init__(self, name: str):
        self.name = name
        self.connected = False
        self.closed = False

    async def connect(self) -> str:
        await asyncio.sleep(0.01)  # simulate async
        self.connected = True
        return f"Connected-{self.name}"

    async def close(self) -> None:
        await asyncio.sleep(0.01)  # simulate async
        self.closed = True

@pytest.mark.asyncio
async def test_abstract_methods_raise():
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
    conn = DummyConnection("testdb")
    result = await conn.connect()
    assert result == "Connected-testdb"
    assert conn.connected is True

@pytest.mark.asyncio
async def test_concrete_close_marks_closed():
    conn = DummyConnection("testdb")
    await conn.connect()
    await conn.close()
    assert conn.closed is True

def test_init_accepts_parameters():
    conn = DummyConnection("param_test")
    assert conn.name == "param_test"
    assert not conn.connected
    assert not conn.closed
