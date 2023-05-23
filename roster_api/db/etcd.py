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
