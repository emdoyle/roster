import json
import logging
from typing import Optional

from roster_api import constants, errors
from roster_api.constants import WORKFLOW_ROUTER_QUEUE
from roster_api.messaging.inbox import AgentInbox
from roster_api.messaging.rabbitmq import RabbitMQClient, get_rabbitmq
from roster_api.models.workflow import (
    ActionResult,
    ActionRunStatus,
    InitiateWorkflowPayload,
    WorkflowAction,
    WorkflowActionReportPayload,
    WorkflowActionTriggerPayload,
    WorkflowMessage,
    WorkflowRecord,
    WorkflowSpec,
)
from roster_api.services.team import TeamService
from roster_api.services.workflow import WorkflowRecordService, WorkflowService

logger = logging.getLogger(constants.LOGGER_NAME)


def _workflow_inputs_are_valid(workflow_spec: WorkflowSpec, payload_inputs: dict):
    return all(
        (
            required_input.name in payload_inputs
            for required_input in workflow_spec.inputs
        )
    )


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
        elif message.kind == WorkflowActionReportPayload.KEY:
            await self._handle_action_report(message, payload)

    async def _trigger_action(
        self,
        workflow_spec: WorkflowSpec,
        workflow_record: WorkflowRecord,
        action_details: WorkflowAction,
    ):
        # Retrieve the TeamResource associated with this Workflow
        # WARNING: default namespace
        try:
            team_resource = TeamService().get_team(workflow_spec.team)
        except errors.TeamNotFoundError:
            logger.debug("(workflow-router) Team not found")
            logger.warning(
                "Tried to trigger action %s for workflow %s / %s, but team %s not found",
                action_details.action,
                workflow_spec.name,
                workflow_record.id,
                workflow_spec.team,
            )
            return

        # Map workflow context to action inputs
        trigger_payload = WorkflowActionTriggerPayload(
            action=action_details.action,
            inputs={
                k: workflow_record.context[v]
                for k, v in action_details.inputMap.items()
            },
            role_context=team_resource.get_role_description(action_details.role),
        )
        # Trigger the action by sending a message to the agent's inbox
        await AgentInbox.from_role(
            workflow_spec.team, action_details.role, rmq_client=self.rmq
        ).trigger_action(workflow_spec.name, workflow_record.id, trigger_payload)

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

        # Validate inputs match workflow spec inputs
        if not _workflow_inputs_are_valid(workflow_spec, payload.inputs):
            logger.debug("(workflow-router) Invalid inputs")
            logger.warning(
                "Tried to initiate workflow %s with inputs %s, but inputs are invalid",
                message.workflow,
                payload.inputs,
            )
            return

        for _, action_details in workflow_spec.actions.items():
            # If all dependencies are satisfied, trigger the action
            if all(
                [
                    dep in workflow_record.context
                    for dep in action_details.inputMap.values()
                ]
            ):
                logger.debug(
                    "(workflow-router) Triggering action %s", action_details.action
                )
                await self._trigger_action(
                    workflow_spec=workflow_spec,
                    workflow_record=workflow_record,
                    action_details=action_details,
                )

    async def _handle_action_report(
        self, message: WorkflowMessage, payload: WorkflowActionReportPayload
    ):
        try:
            workflow_record = WorkflowRecordService().get_workflow_record(
                message.workflow, message.id
            )
        except errors.WorkflowRecordNotFoundError:
            logger.debug("(workflow-router) Workflow record not found")
            logger.warning(
                "Tried to handle action report %s for workflow %s / %s, but record not found",
                payload.action,
                message.workflow,
                message.id,
            )
            return

        try:
            workflow_resource = WorkflowService().get_workflow(message.workflow)
        except errors.WorkflowNotFoundError:
            logger.debug("(workflow-router) Workflow not found")
            logger.warning(
                "Tried to handle action report %s for workflow %s / %s, but workflow not found",
                payload.action,
                message.workflow,
                message.id,
            )
            return
        workflow_spec = workflow_resource.spec
        # Store the action's outputs in the workflow record's context
        action_outputs = {
            f"{payload.action}.{output_key}": output_value
            for output_key, output_value in payload.outputs.items()
        }
        workflow_record.context.update(action_outputs)
        # Update the action's run status in the workflow record
        run_status = workflow_record.run_status.get(payload.action, ActionRunStatus())
        run_status.runs += 1
        run_status.results.append(
            ActionResult(outputs=payload.outputs, error=payload.error)
        )
        workflow_record.run_status[payload.action] = run_status
        # Update the workflow record in etcd
        try:
            WorkflowRecordService().update_workflow_record(workflow_record)
        except errors.WorkflowRecordNotFoundError:
            logger.debug("(workflow-router) Workflow record not found")
            logger.warning(
                "Tried to update workflow record %s / %s, but record not found",
                message.workflow,
                message.id,
            )
            return

        # Trigger the appropriate action messages
        for _, action_details in workflow_spec.actions.items():
            dependencies_satisfied = all(
                [
                    dep in workflow_record.context
                    for dep in action_details.inputMap.values()
                ]
            )
            if not dependencies_satisfied:
                continue

            action_run_config = action_details.runConfig
            action_run_status = workflow_record.run_status.get(
                action_details.action, ActionRunStatus()
            )
            action_failed = (
                action_run_status.results and action_run_status.results[-1].error
            )

            if action_run_status.runs == 0:
                # If the action hasn't been triggered yet, trigger it
                await self._trigger_action(
                    workflow_spec=workflow_spec,
                    workflow_record=workflow_record,
                    action_details=action_details,
                )
            elif (
                action_failed
                and action_run_config.num_retries >= action_run_status.runs
            ):
                # If the action errored, and we haven't reached the max number of retries,
                # trigger the action again
                await self._trigger_action(
                    workflow_spec=workflow_spec,
                    workflow_record=workflow_record,
                    action_details=action_details,
                )
