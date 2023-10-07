import logging
from typing import Optional

from qdrant_client import QdrantClient
from roster_api import constants, settings

QDRANT_CLIENT: Optional[QdrantClient] = None

logger = logging.getLogger(constants.LOGGER_NAME)


def get_qdrant_client() -> QdrantClient:
    global QDRANT_CLIENT
    if QDRANT_CLIENT is not None:
        return QDRANT_CLIENT

    QDRANT_CLIENT = QdrantClient(
        location=settings.QDRANT_HOST, port=settings.QDRANT_PORT
    )
    return QDRANT_CLIENT
