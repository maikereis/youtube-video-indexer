import pytest
from unittest.mock import patch, MagicMock
from elasticsearch import AsyncElasticsearch
from ytindexer.database import ElasticConnection

def test_elastic_connection_singleton():
    with patch('ytindexer.database.elastic.AsyncElasticsearch') as mock_client:
        # Create a mock instance to be returned by AsyncElasticsearch
        mock_instance = MagicMock(spec=AsyncElasticsearch)
        mock_client.return_value = mock_instance

        # Instantiate ElasticConnection twice
        client1 = ElasticConnection()
        client2 = ElasticConnection()

        # Assert that AsyncElasticsearch was called only once
        mock_client.assert_called_once()

        # Assert that both instances are the same (singleton behavior)
        assert client1 is client2
