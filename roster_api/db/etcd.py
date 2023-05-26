import logging
import time
from typing import Optional

import etcd3
from roster_api import constants, errors, settings

ETCD_CLIENT: Optional[etcd3.Etcd3Client] = None

logger = logging.getLogger(constants.LOGGER_NAME)


def get_etcd_client() -> etcd3.Etcd3Client:
    global ETCD_CLIENT
    if ETCD_CLIENT is not None:
        return ETCD_CLIENT

    import etcd3

    ETCD_CLIENT = etcd3.client(host=settings.ETCD_HOST, port=settings.ETCD_PORT)
    return ETCD_CLIENT


def wait_for_etcd(
    client: Optional[etcd3.Etcd3Client] = None, retries: int = 10, delay: float = 1
):
    client = client or get_etcd_client()
    for i in range(retries):
        try:
            status = client.status()
            logger.debug("(wait_for_etcd): Connected (version: %s)", status.version)
            return
        except (
            etcd3.exceptions.ConnectionFailedError,
            etcd3.exceptions.ConnectionTimeoutError,
        ):
            logger.debug("(wait_for_etcd): Failed to connect to etcd")
            if i < retries - 1:
                logger.debug("(wait_for_etcd): Retrying in %s seconds", delay)
                time.sleep(delay)
            else:
                logger.debug("(wait_for_etcd): No more retries")
                raise errors.RosterAPIError(
                    "Failed to connect to etcd to watch resources."
                )
