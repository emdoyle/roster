import time
from typing import TYPE_CHECKING, Optional

from roster_api import settings

if TYPE_CHECKING:
    import etcd3

ETCD_CLIENT: Optional["etcd3.Etcd3Client"] = None


def get_etcd_client() -> "etcd3.Etcd3Client":
    global ETCD_CLIENT
    if ETCD_CLIENT is not None:
        return ETCD_CLIENT

    import etcd3

    ETCD_CLIENT = etcd3.client(host=settings.ETCD_HOST, port=settings.ETCD_PORT)
    return ETCD_CLIENT


def wait_for_etcd(
    client: Optional["etcd3.Etcd3Client"] = None, retries: int = 10, delay: float = 1
):
    client = client or get_etcd_client()
    for i in range(retries):
        try:
            print(f"(wait_for_etcd): {client.status()}")
            return
        except (
            etcd3.exceptions.ConnectionFailedError,
            etcd3.exceptions.ConnectionTimeoutError,
        ):
            if i < retries - 1:  # If not the last attempt
                time.sleep(delay)  # Wait a bit before trying again
            else:
                raise  # Re-raise the last exception
