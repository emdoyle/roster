import logging
import uuid
from typing import Optional

import etcd3
from roster_api import constants, errors
from roster_api.constants import WORKFLOW_ROUTER_QUEUE
from roster_api.db.etcd import get_etcd_client
from roster_api.messaging.rabbitmq import RabbitMQClient, get_rabbitmq
from roster_api.models.workflow import WorkflowRecord, WorkflowResource, WorkflowSpec

logger = logging.getLogger(constants.LOGGER_NAME)


class WorkflowService:
    KEY_PREFIX = "/registry/workflows"
    DEFAULT_NAMESPACE = "default"

    def __init__(
        self,
        etcd_client: Optional[etcd3.Etcd3Client] = None,
        rmq_client: Optional[RabbitMQClient] = None,
    ):
        self.etcd_client: etcd3.Etcd3Client = etcd_client or get_etcd_client()
        self.rmq: RabbitMQClient = rmq_client or get_rabbitmq()

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
        logger.debug("Updated Workflow %s.", workflow.name)
        return workflow_resource

    def delete_workflow(self, name: str, namespace: str = DEFAULT_NAMESPACE) -> bool:
        workflow_key = self._get_workflow_key(name, namespace)
        deleted = self.etcd_client.delete(workflow_key)
        if deleted:
            logger.debug("Deleted Workflow %s.", name)
        return deleted

    async def initiate_workflow(self, workflow_name: str, inputs: dict):
        workflow = self.get_workflow(workflow_name)
        logger.debug(
            "Sent message to initiate workflow %s with inputs: %s",
            workflow_name,
            inputs,
        )
        await self.rmq.publish_json(
            WORKFLOW_ROUTER_QUEUE,
            {
                "id": str(uuid.uuid4()),
                "workflow": workflow,
                "kind": "initiate_workflow",
                "data": inputs,
            },
        )


class WorkflowRecordService:
    KEY_PREFIX = "/records/workflows"
    DEFAULT_NAMESPACE = "default"

    def __init__(self, etcd_client: Optional[etcd3.Etcd3Client] = None):
        self.etcd_client: etcd3.Etcd3Client = etcd_client or get_etcd_client()

    def _get_workflow_key(
        self, workflow_name: str, namespace: str = DEFAULT_NAMESPACE
    ) -> str:
        return f"{self.KEY_PREFIX}/{namespace}/{workflow_name}"

    def _get_record_key(
        self, workflow_name: str, record_id: str, namespace: str = DEFAULT_NAMESPACE
    ) -> str:
        return (
            f"{self._get_workflow_key(workflow_name, namespace=namespace)}/{record_id}"
        )

    def create_workflow_record(
        self,
        workflow_name: str,
        context: Optional[dict] = None,
        namespace: str = DEFAULT_NAMESPACE,
    ) -> WorkflowRecord:
        workflow_record = WorkflowRecord(name=workflow_name, context=context or {})
        record_key = self._get_record_key(
            workflow_name, workflow_record.id, namespace=namespace
        )
        created = self.etcd_client.put_if_not_exists(
            record_key, workflow_record.serialize()
        )
        if not created:
            raise errors.WorkflowRecordAlreadyExistsError(
                workflow=workflow_name, record=workflow_record.id
            )
        logger.debug(
            "Created WorkflowRecord %s / %s", workflow_record.name, workflow_record.id
        )
        return workflow_record

    def get_workflow_record(
        self, workflow_name: str, record_id: str, namespace: str = DEFAULT_NAMESPACE
    ) -> WorkflowRecord:
        record_key = self._get_record_key(workflow_name, record_id, namespace=namespace)
        record_data, _ = self.etcd_client.get(record_key)
        if not record_data:
            raise errors.WorkflowRecordNotFoundError(
                workflow=workflow_name, record=record_id
            )
        return WorkflowRecord.deserialize_from_etcd(record_data)

    def list_workflow_records(
        self, workflow_name: str, namespace: str = DEFAULT_NAMESPACE
    ) -> list[WorkflowRecord]:
        workflow_key = self._get_workflow_key(workflow_name, namespace=namespace)
        workflow_record_data = self.etcd_client.get_prefix(workflow_key)
        return [
            WorkflowRecord.deserialize_from_etcd(data)
            for data, _ in workflow_record_data
        ]

    def update_workflow_record(
        self, workflow_record: WorkflowRecord, namespace: str = DEFAULT_NAMESPACE
    ) -> WorkflowRecord:
        record_key = self._get_record_key(
            workflow_record.name, workflow_record.id, namespace=namespace
        )
        current_record, _ = self.etcd_client.get(record_key)
        if not current_record:
            raise errors.WorkflowRecordNotFoundError(
                workflow=workflow_record.name, record=workflow_record.id
            )
        self.etcd_client.put(record_key, workflow_record.serialize())
        logger.debug(
            "Updated Workflow Record %s / %s", workflow_record.name, workflow_record.id
        )
        return workflow_record

    def delete_workflow_record(
        self, workflow_name: str, record_id: str, namespace: str = DEFAULT_NAMESPACE
    ) -> bool:
        record_key = self._get_record_key(workflow_name, record_id, namespace=namespace)
        deleted = self.etcd_client.delete(record_key)
        if deleted:
            logger.debug("Deleted Workflow Record %s / %s", workflow_name, record_id)
        return deleted