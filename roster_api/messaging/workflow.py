import json
import logging
from typing import Optional

from roster_api import constants, errors
from roster_api.constants import WORKFLOW_ROUTER_QUEUE
from roster_api.messaging.inbox import AgentInbox
from roster_api.messaging.rabbitmq import RabbitMQClient, get_rabbitmq
from roster_api.models.workflow import (
    InitiateWorkflowPayload,
    WorkflowActionTriggerPayload,
    WorkflowMessage,
)
from roster_api.services.workflow import WorkflowRecordService, WorkflowService

logger = logging.getLogger(constants.LOGGER_NAME)


class WorkflowRouter:
    def __init__(self, rmq_client: Optional[RabbitMQClient] = None):
        self.rmq: RabbitMQClient = rmq_client or get_rabbitmq()

    async def setup(self) -> None:
        await self.rmq.register_callback(WORKFLOW_ROUTER_QUEUE, self.route)

    async def teardown(self) -> None:
        await self.rmq.deregister_callback(WORKFLOW_ROUTER_QUEUE, self.route)

    async def route(self, message: str) -> None:
        try:
            data = json.loads(message)
            message = WorkflowMessage(**data)
            payload = message.read_contents()
        except json.JSONDecodeError:
            logger.debug(
                "(workflow-router) Failed to decode workflow message as JSON: %s",
                message,
            )
            return
        except (TypeError, ValueError) as e:
            logger.debug(
                "(workflow-router) Failed to decode workflow message as WorkflowMessage: %s (%s)",
                message,
                e,
            )
            return

        logger.debug("(workflow-router) Received workflow message: %s", message)
        if message.kind == InitiateWorkflowPayload.KEY:
            await self._handle_initiate_workflow(message, payload)

    async def _handle_initiate_workflow(
        self, message: WorkflowMessage, payload: InitiateWorkflowPayload
    ):
        try:
            workflow_record = WorkflowRecordService().create_workflow_record(
                message.workflow, payload.inputs
            )
        except errors.WorkflowRecordAlreadyExistsError:
            logger.debug("(workflow-router) Workflow record already exists")
            logger.warning(
                "Tried to initiate workflow %s with inputs %s, but record already exists",
                message.workflow,
                payload.inputs,
            )
            return

        workflow_resource = WorkflowService().get_workflow(message.workflow)
        workflow_spec = workflow_resource.spec
        for _, action_details in workflow_spec.actions.items():
            # If all dependencies are satisfied, trigger the action
            if all(
                [
                    dep in workflow_record.context
                    for dep in action_details.inputMap.values()
                ]
            ):
                # Map workflow context to action inputs
                trigger_payload = WorkflowActionTriggerPayload(
                    action=action_details.action,
                    inputs={
                        k: workflow_record.context[v]
                        for k, v in action_details.inputMap.items()
                    },
                )
                # Trigger the action by sending a message to the agent's inbox
                await AgentInbox.from_role(
                    workflow_spec.team, action_details.role, rmq_client=self.rmq
                ).trigger_action(message.workflow, workflow_record.id, trigger_payload)
