"""
Dependency providers for the YTIndexer application.

This module provides factory functions for commonly used dependencies,
such as rate limiters, notification queues, and Elasticsearch connections.

These functions are designed to be used with FastAPI's dependency injection system.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from ytindexer.database import ValkeyConnection, ElasticConnection, MongoConnection
from ytindexer.queues import NotificationQueue
from ytindexer.config import settings


def get_limiter() -> Limiter:
    """Create a rate limiter instance.

    The limiter restricts clients to 500 requests per minute based on their remote address.

    Returns:
        Limiter: An instance of the SlowAPI Limiter.
    """
    return Limiter(
        key_func=get_remote_address,
        default_limits=["500/minute"],
    )


async def get_notification_queue() -> NotificationQueue:
    """Create and return a NotificationQueue instance.

    Connects to the Valkey (Redis) server configured in the settings,
    and creates a notification queue named 'notification-queue'.

    Returns:
        NotificationQueue: An instance for managing notification messages.
    """
    client = await ValkeyConnection(
        host=settings.valkey.host,
        port=settings.valkey.port,
        password=settings.valkey.password.get_secret_value(),
    ).connect()
    return NotificationQueue(client, "notification-queue")


async def get_elastic_connection() -> ElasticConnection:
    """Create and return an Elasticsearch connection instance.

    Connects to the Elasticsearch cluster using the DSN specified in the settings.

    Returns:
        ElasticConnection: An instance connected to the Elasticsearch cluster.
    """
    client = await ElasticConnection(settings.search.dsn).connect()
    return client


async def get_mongo_connection() -> MongoConnection:
    """Create and return an MongoDB connection instance.

    Connects to the MongoDB using the DSN specified in the settings.

    Returns:
        MongoDB: An instance connected to the MongoDB.
    """
    client = await MongoConnection(settings.mongo.dsn).connect()
    return client
