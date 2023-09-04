import logging
from typing import Optional

import etcd3
from roster_api import constants, errors
from roster_api.db.etcd import get_etcd_client
from roster_api.models.identity import IdentityResource, IdentitySpec
from roster_api.util.serialization import deserialize_from_etcd, serialize

logger = logging.getLogger(constants.LOGGER_NAME)


class IdentityService:
    KEY_PREFIX = "/resources/identities"
    DEFAULT_NAMESPACE = "default"

    def __init__(self, etcd_client: Optional[etcd3.Etcd3Client] = None):
        self.etcd_client: etcd3.Etcd3Client = etcd_client or get_etcd_client()

    def _get_identity_key(
        self, identity_name: str, namespace: str = DEFAULT_NAMESPACE
    ) -> str:
        return f"{self.KEY_PREFIX}/{namespace}/{identity_name}"

    def create_identity(
        self, identity: IdentitySpec, namespace: str = DEFAULT_NAMESPACE
    ) -> IdentityResource:
        identity_key = self._get_identity_key(identity.name, namespace)
        identity_resource = IdentityResource.initial_state(spec=identity)
        created = self.etcd_client.put_if_not_exists(
            identity_key, serialize(identity_resource)
        )
        if not created:
            raise errors.IdentityAlreadyExistsError(identity=identity)
        logger.debug("Created Identity %s", identity.name)
        return identity_resource

    def get_identity(
        self, name: str, namespace: str = DEFAULT_NAMESPACE
    ) -> IdentityResource:
        identity_key = self._get_identity_key(name, namespace)
        identity_data, _ = self.etcd_client.get(identity_key)
        if not identity_data:
            raise errors.IdentityNotFoundError(identity=name)
        return deserialize_from_etcd(IdentityResource, identity_data)

    def list_identities(
        self, namespace: str = DEFAULT_NAMESPACE
    ) -> list[IdentityResource]:
        identity_key = self._get_identity_key("", namespace)
        identity_data = self.etcd_client.get_prefix(identity_key)
        return [
            deserialize_from_etcd(IdentityResource, data) for data, _ in identity_data
        ]

    def update_identity(
        self, identity: IdentitySpec, namespace: str = DEFAULT_NAMESPACE
    ) -> IdentityResource:
        identity_key = self._get_identity_key(identity.name, namespace)
        identity_resource = self.get_identity(identity.name, namespace)
        identity_resource.spec = identity
        self.etcd_client.put(identity_key, serialize(identity_resource))
        logger.debug(f"Updated Identity {identity.name}.")
        return identity_resource

    def delete_identity(self, name: str, namespace: str = DEFAULT_NAMESPACE) -> bool:
        identity_key = self._get_identity_key(name, namespace)
        deleted = self.etcd_client.delete(identity_key)
        if deleted:
            logger.debug(f"Deleted Identity {name}.")
        return deleted
