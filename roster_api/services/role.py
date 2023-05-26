import logging
from typing import Optional

import etcd3
from roster_api import constants, errors
from roster_api.db.etcd import get_etcd_client
from roster_api.models.role import RoleResource, RoleSpec

logger = logging.getLogger(constants.LOGGER_NAME)


class RoleService:
    KEY_PREFIX = "/registry/roles"
    DEFAULT_NAMESPACE = "default"

    def __init__(self, etcd_client: Optional[etcd3.Etcd3Client] = None):
        self.etcd_client: etcd3.Etcd3Client = etcd_client or get_etcd_client()

    def _get_role_key(self, role_name: str, namespace: str = DEFAULT_NAMESPACE) -> str:
        return f"{self.KEY_PREFIX}/{namespace}/{role_name}"

    def create_role(
        self, role: RoleSpec, namespace: str = DEFAULT_NAMESPACE
    ) -> RoleResource:
        role_key = self._get_role_key(role.name, namespace)
        role_resource = RoleResource.initial_state(spec=role)
        created = self.etcd_client.put_if_not_exists(
            role_key, role_resource.serialize()
        )
        if not created:
            raise errors.RoleAlreadyExistsError(role=role)
        logger.debug("Created Role %s", role.name)
        return role_resource

    def get_role(self, name: str, namespace: str = DEFAULT_NAMESPACE) -> RoleResource:
        role_key = self._get_role_key(name, namespace)
        role_data, _ = self.etcd_client.get(role_key)
        if not role_data:
            raise errors.RoleNotFoundError(role=name)
        return RoleResource.deserialize_from_etcd(role_data)

    def list_roles(self, namespace: str = DEFAULT_NAMESPACE) -> list[RoleResource]:
        role_key = self._get_role_key("", namespace)
        role_data = self.etcd_client.get_prefix(role_key)
        return [RoleResource.deserialize_from_etcd(data) for data, _ in role_data]

    def update_role(
        self, role: RoleSpec, namespace: str = DEFAULT_NAMESPACE
    ) -> RoleResource:
        role_key = self._get_role_key(role.name, namespace)
        role_resource = self.get_role(role.name, namespace)
        role_resource.spec = role
        self.etcd_client.put(role_key, role_resource.serialize())
        logger.debug(f"Updated Role {role.name}.")
        return role_resource

    def delete_role(self, name: str, namespace: str = DEFAULT_NAMESPACE) -> bool:
        role_key = self._get_role_key(name, namespace)
        deleted = self.etcd_client.delete(role_key)
        if deleted:
            logger.debug(f"Deleted Role {name}.")
        return deleted
