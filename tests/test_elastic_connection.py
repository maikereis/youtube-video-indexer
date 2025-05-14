import os

import pytest
from dotenv import load_dotenv
from elasticsearch import AsyncElasticsearch

load_dotenv()  # Load variables from .env

@pytest.mark.asyncio
async def test_elasticsearch_connection():
    host = os.getenv("ELASTIC_HOST", "localhost")
    port = os.getenv("ELASTIC_PORT", "9200")
    url = f"http://{host}:{port}"

    es = AsyncElasticsearch(hosts=[url])

    try:
        is_alive = await es.ping()
        assert is_alive, "Elasticsearch did not respond to ping"
    except Exception as e:
        pytest.fail(f"Error pinging Elasticsearch: {e}")
    finally:
        await es.close()
