import logging
import uuid
from typing import Optional

import etcd3
from code_index import constants, errors
from code_index.constants import WORKFLOW_ROUTER_QUEUE
from code_index.db.etcd import get_etcd_client
from code_index.messaging.rabbitmq import RabbitMQClient, get_rabbitmq
from code_index.models.common import TypedResult
from code_index.models.workflow import (
    WorkflowDerivedState,
    WorkflowRecord,
    WorkflowResource,
    WorkflowSpec,
)
from code_index.util.serialization import deserialize_from_etcd, serialize

logger = logging.getLogger(constants.LOGGER_NAME)


class WorkflowService:
    KEY_PREFIX = "/resources/workflows"
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
        workflow.update_derived_state()
        workflow_resource = WorkflowResource.initial_state(spec=workflow)
        created = self.etcd_client.put_if_not_exists(
            workflow_key, serialize(workflow_resource)
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
        return deserialize_from_etcd(WorkflowResource, workflow_data)

    def list_workflows(
        self, namespace: str = DEFAULT_NAMESPACE
    ) -> list[WorkflowResource]:
        workflow_key = self._get_workflow_key("", namespace)
        workflow_data = self.etcd_client.get_prefix(workflow_key)
        return [
            deserialize_from_etcd(WorkflowResource, data) for data, _ in workflow_data
        ]

    def update_workflow(
        self, workflow: WorkflowSpec, namespace: str = DEFAULT_NAMESPACE
    ) -> WorkflowResource:
        workflow_key = self._get_workflow_key(workflow.name, namespace)
        workflow.update_derived_state()
        workflow_resource = self.get_workflow(workflow.name, namespace)
        workflow_resource.spec = workflow
        self.etcd_client.put(workflow_key, serialize(workflow_resource))
        logger.debug("Updated Workflow %s.", workflow.name)
        return workflow_resource

    def delete_workflow(self, name: str, namespace: str = DEFAULT_NAMESPACE) -> bool:
        workflow_key = self._get_workflow_key(name, namespace)
        deleted = self.etcd_client.delete(workflow_key)
        if deleted:
            logger.debug("Deleted Workflow %s.", name)
        return deleted

    async def initiate_workflow(
        self, workflow_name: str, inputs: dict, workspace_name: str = ""
    ):
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
                "workflow": workflow.spec.name,
                "kind": "initiate_workflow",
                "data": {"inputs": inputs, "workspace": workspace_name},
            },
        )


class WorkflowRecordService:
    KEY_PREFIX = "/records/workflows"
    DEFAULT_NAMESPACE = "default"

    def __init__(self, etcd_client: Optional[etcd3.Etcd3Client] = None):
        self.etcd_client: etcd3.Etcd3Client = etcd_client or get_etcd_client()

    def _get_base_key(self, namespace: str = DEFAULT_NAMESPACE) -> str:
        return f"{self.KEY_PREFIX}/{namespace}"

    def _get_workflow_key(
        self, workflow_name: str, namespace: str = DEFAULT_NAMESPACE
    ) -> str:
        return f"{self._get_base_key(namespace=namespace)}/{workflow_name}"

    def _get_record_key(
        self, workflow_name: str, record_id: str, namespace: str = DEFAULT_NAMESPACE
    ) -> str:
        return (
            f"{self._get_workflow_key(workflow_name, namespace=namespace)}/{record_id}"
        )

    def create_workflow_record(
        self,
        workflow_spec: WorkflowSpec,
        inputs: Optional[dict] = None,
        workspace_name: str = "",
        namespace: str = DEFAULT_NAMESPACE,
    ) -> WorkflowRecord:
        # NOTE: implied that inputs are validated, might want to move that here
        context = {
            f"workflow.{input_signature.name}": TypedResult(
                type=input_signature.type, value=inputs[input_signature.name]
            )
            for input_signature in workflow_spec.inputs
        }
        workflow_name = workflow_spec.name
        workflow_record = WorkflowRecord(
            name=workflow_name,
            spec=workflow_spec,
            context=context,
            workspace=workspace_name,
        )
        record_key = self._get_record_key(
            workflow_name, workflow_record.id, namespace=namespace
        )
        created = self.etcd_client.put_if_not_exists(
            record_key, serialize(workflow_record)
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
        # TODO: should allow retrieving by record_id alone.
        #  a principled approach to retrieving efficiently by ID alone could be to maintain
        #  an in-memory index of ID to name
        #  which is built on startup and maintained via etcd watcher/informer mechanisms
        record_key = self._get_record_key(workflow_name, record_id, namespace=namespace)
        record_data, _ = self.etcd_client.get(record_key)
        if not record_data:
            raise errors.WorkflowRecordNotFoundError(
                workflow=workflow_name, record=record_id
            )
        return deserialize_from_etcd(WorkflowRecord, record_data)

    def list_workflow_records(
        self, workflow_name: str = "", namespace: str = DEFAULT_NAMESPACE
    ) -> list[WorkflowRecord]:
        if workflow_name:
            workflow_key = self._get_workflow_key(workflow_name, namespace=namespace)
        else:
            workflow_key = self._get_base_key(namespace=namespace)
        workflow_record_data = self.etcd_client.get_prefix(workflow_key)

        return [
            deserialize_from_etcd(WorkflowRecord, data)
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
        self.etcd_client.put(record_key, serialize(workflow_record))
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
