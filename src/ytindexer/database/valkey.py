import valkey

from ytindexer.config import settings
from ytindexer.logging import logger


class ValkeyConnection:
    _instance: valkey.client.Valkey | None = None

    def __new__(cls, *args, **kwargs) -> valkey.client.Valkey:
        if cls._instance is None:
            try:
                cls._instance = valkey.Valkey(
                    host=settings.valkey.host,
                    port=settings.valkey.port,
                    username=None,
                    password=settings.valkey.password.get_secret_value(),
                    db=0,
                )
                cls._instance.ping()
            except valkey.exceptions.ConnectionError as conn_fail:
                logger.error("Couldn't connect to the Valkey: {error}", error=conn_fail)
                raise

        logger.info(
            "Successfully connected to Valkey at: {host}", host=settings.valkey.host
        )
        return cls._instance