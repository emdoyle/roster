import logging
from typing import Optional

import etcd3
from code_index import constants, errors
from code_index.db.etcd import get_etcd_client
from code_index.models.workspace import Workspace
from code_index.util.serialization import deserialize_from_etcd, serialize

logger = logging.getLogger(constants.LOGGER_NAME)


class WorkspaceService:
    KEY_PREFIX = "/workspaces"
    DEFAULT_NAMESPACE = "default"

    def __init__(self, etcd_client: Optional[etcd3.Etcd3Client] = None):
        self.etcd_client: etcd3.Etcd3Client = etcd_client or get_etcd_client()

    def _get_workspace_key(
        self, workspace_name: str, namespace: str = DEFAULT_NAMESPACE
    ) -> str:
        return f"{self.KEY_PREFIX}/{namespace}/{workspace_name}"

    def create_workspace(
        self, workspace: Workspace, namespace: str = DEFAULT_NAMESPACE
    ) -> Workspace:
        workspace_key = self._get_workspace_key(workspace.name, namespace)
        created = self.etcd_client.put_if_not_exists(
            workspace_key, serialize(workspace)
        )
        if not created:
            raise errors.WorkspaceAlreadyExistsError(workspace=workspace)
        logger.debug("Created Workspace %s", workspace.name)
        return workspace

    def get_workspace(self, name: str, namespace: str = DEFAULT_NAMESPACE) -> Workspace:
        workspace_key = self._get_workspace_key(name, namespace)
        workspace_data, _ = self.etcd_client.get(workspace_key)
        if not workspace_data:
            raise errors.WorkspaceNotFoundError(workspace=name)
        return deserialize_from_etcd(Workspace, workspace_data)

    def list_workspaces(self, namespace: str = DEFAULT_NAMESPACE) -> list[Workspace]:
        workspace_key = self._get_workspace_key("", namespace)
        workspace_data = self.etcd_client.get_prefix(workspace_key)
        return [deserialize_from_etcd(Workspace, data) for data, _ in workspace_data]

    def update_or_create_workspace(
        self, workspace: Workspace, namespace: str = DEFAULT_NAMESPACE
    ) -> Workspace:
        workspace_key = self._get_workspace_key(workspace.name, namespace)
        self.etcd_client.put(workspace_key, serialize(workspace))
        logger.debug("Updated Workspace %s.", workspace.name)
        return workspace

    def delete_workspace(self, name: str, namespace: str = DEFAULT_NAMESPACE) -> bool:
        workspace_key = self._get_workspace_key(name, namespace)
        deleted = self.etcd_client.delete(workspace_key)
        if deleted:
            logger.debug("Deleted Workspace %s.", name)
        return deleted
