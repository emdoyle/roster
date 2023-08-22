import logging
from typing import Optional

import etcd3
from roster_api import constants, errors
from roster_api.db.etcd import get_etcd_client
from roster_api.models.workflow import WorkflowResource, WorkflowSpec

logger = logging.getLogger(constants.LOGGER_NAME)


class WorkflowService:
    KEY_PREFIX = "/registry/workflows"
    DEFAULT_NAMESPACE = "default"

    def __init__(self, etcd_client: Optional[etcd3.Etcd3Client] = None):
        self.etcd_client: etcd3.Etcd3Client = etcd_client or get_etcd_client()

    def _get_workflow_key(
        self, workflow_name: str, namespace: str = DEFAULT_NAMESPACE
    ) -> str:
        return f"{self.KEY_PREFIX}/{namespace}/{workflow_name}"

    def create_workflow(
        self, workflow: WorkflowSpec, namespace: str = DEFAULT_NAMESPACE
    ) -> WorkflowResource:
        workflow_key = self._get_workflow_key(workflow.name, namespace)
        workflow_resource = WorkflowResource.initial_state(spec=workflow)
        created = self.etcd_client.put_if_not_exists(
            workflow_key, workflow_resource.serialize()
        )
        if not created:
            raise errors.WorkflowAlreadyExistsError(workflow=workflow)
        logger.debug("Created Workflow %s", workflow.name)
        return workflow_resource

    def get_workflow(
        self, name: str, namespace: str = DEFAULT_NAMESPACE
    ) -> WorkflowResource:
        workflow_key = self._get_workflow_key(name, namespace)
        workflow_data, _ = self.etcd_client.get(workflow_key)
        if not workflow_data:
            raise errors.WorkflowNotFoundError(workflow=name)
        return WorkflowResource.deserialize_from_etcd(workflow_data)

    def list_workflows(
        self, namespace: str = DEFAULT_NAMESPACE
    ) -> list[WorkflowResource]:
        workflow_key = self._get_workflow_key("", namespace)
        workflow_data = self.etcd_client.get_prefix(workflow_key)
        return [
            WorkflowResource.deserialize_from_etcd(data) for data, _ in workflow_data
        ]

    def update_workflow(
        self, workflow: WorkflowSpec, namespace: str = DEFAULT_NAMESPACE
    ) -> WorkflowResource:
        workflow_key = self._get_workflow_key(workflow.name, namespace)
        workflow_resource = self.get_workflow(workflow.name, namespace)
        workflow_resource.spec = workflow
        self.etcd_client.put(workflow_key, workflow_resource.serialize())
        logger.debug(f"Updated Workflow {workflow.name}.")
        return workflow_resource

    def delete_workflow(self, name: str, namespace: str = DEFAULT_NAMESPACE) -> bool:
        workflow_key = self._get_workflow_key(name, namespace)
        deleted = self.etcd_client.delete(workflow_key)
        if deleted:
            logger.debug(f"Deleted Workflow {name}.")
        return deleted
