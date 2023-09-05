import asyncio
import json
import logging
from typing import Awaitable, Callable, Optional

from roster_api import constants, errors
from roster_api.constants import WORKFLOW_ROUTER_QUEUE
from roster_api.messaging.inbox import AgentInbox
from roster_api.messaging.rabbitmq import RabbitMQClient, get_rabbitmq
from roster_api.models.workflow import (
    InitiateWorkflowPayload,
    StepResult,
    StepRunStatus,
    WorkflowActionReportPayload,
    WorkflowActionTriggerPayload,
    WorkflowFinishEvent,
    WorkflowMessage,
    WorkflowRecord,
    WorkflowResource,
    WorkflowSpec,
    WorkflowStartEvent,
    WorkflowStep,
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
        self.workflow_start_listeners = []
        self.workflow_finish_listeners = []

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
        step: str,
        step_details: WorkflowStep,
    ):
        # Retrieve the TeamResource associated with this Workflow
        # WARNING: default namespace
        try:
            team_resource = TeamService().get_team(workflow_spec.team)
        except errors.TeamNotFoundError:
            logger.debug("(workflow-router) Team not found")
            logger.warning(
                "Tried to trigger step %s (%s) for workflow %s / %s, but team %s not found",
                step,
                step_details.action,
                workflow_spec.name,
                workflow_record.id,
                workflow_spec.team,
            )
            return

        # Map workflow context to action inputs
        trigger_payload = WorkflowActionTriggerPayload(
            step=step,
            action=step_details.action,
            inputs={
                k: workflow_record.context[v] for k, v in step_details.inputMap.items()
            },
            role_context=team_resource.get_role_description(step_details.role),
        )
        # Trigger the action by sending a message to the agent's inbox
        await AgentInbox.from_role(
            workflow_spec.team, step_details.role, rmq_client=self.rmq
        ).trigger_action(workflow_spec.name, workflow_record.id, trigger_payload)

    async def _handle_initiate_workflow(
        self, message: WorkflowMessage, payload: InitiateWorkflowPayload
    ):
        try:
            workflow_record = WorkflowRecordService().create_workflow_record(
                message.workflow,
                inputs=payload.inputs,
                workspace_name=payload.workspace,
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

        # Notify listeners that the workflow has started
        asyncio.create_task(
            self._notify_workflow_started(
                workflow=workflow_resource, workflow_record=workflow_record
            )
        )

        for step_name, step_details in workflow_spec.steps.items():
            # If all dependencies are satisfied, trigger the action
            if all(
                [
                    dep in workflow_record.context
                    for dep in step_details.inputMap.values()
                ]
            ):
                logger.debug(
                    "(workflow-router) Triggering step %s (%s)",
                    step_name,
                    step_details.action,
                )
                await self._trigger_action(
                    workflow_spec=workflow_spec,
                    workflow_record=workflow_record,
                    step=step_name,
                    step_details=step_details,
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
        try:
            output_map = workflow_spec.steps[payload.step].outputMap
        except KeyError:
            logger.debug("(workflow-router) Step not found")
            logger.warning(
                "Tried to handle action report %s for workflow %s / %s, but step '%s' not found",
                payload.action,
                message.workflow,
                message.id,
                payload.step,
            )
            return

        # Update the workflow record with the action's results
        if payload.error:
            workflow_record.errors.update(
                {output_key: payload.error for output_key in output_map.keys()}
            )
        else:
            for output_key, output_value in payload.outputs.items():
                if output_key in output_map:
                    workflow_output_key = output_map[output_key]
                    workflow_record.outputs[workflow_output_key] = output_value

        action_outputs = {
            f"{payload.step}.{output_key}": output_value
            for output_key, output_value in payload.outputs.items()
        }
        workflow_record.context.update(action_outputs)

        # Update the action's run status in the workflow record
        run_status = workflow_record.run_status.get(payload.step, StepRunStatus())
        run_status.runs += 1
        run_status.results.append(
            StepResult(outputs=payload.outputs, error=payload.error)
        )
        workflow_record.run_status[payload.step] = run_status

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

        # Determine whether the workflow is finished
        required_outputs = {output.name for output in workflow_spec.outputs}
        if (
            workflow_record.outputs.keys() | workflow_record.errors.keys()
            == required_outputs
        ):
            asyncio.create_task(
                self._notify_workflow_finished(
                    workflow=workflow_resource, workflow_record=workflow_record
                )
            )
            return

        # Otherwise, trigger the appropriate action messages
        for step_name, step_details in workflow_spec.steps.items():
            dependencies_satisfied = all(
                [
                    dep in workflow_record.context
                    for dep in step_details.inputMap.values()
                ]
            )
            if not dependencies_satisfied:
                continue

            step_run_config = step_details.runConfig
            step_run_status = workflow_record.run_status.get(step_name, StepRunStatus())
            action_failed = (
                step_run_status.results and step_run_status.results[-1].error
            )

            if step_run_status.runs == 0:
                # If the action hasn't been triggered yet, trigger it
                await self._trigger_action(
                    workflow_spec=workflow_spec,
                    workflow_record=workflow_record,
                    step=step_name,
                    step_details=step_details,
                )
            elif action_failed and step_run_config.num_retries >= step_run_status.runs:
                # If the action errored, and we haven't reached the max number of retries,
                # trigger the action again
                await self._trigger_action(
                    workflow_spec=workflow_spec,
                    workflow_record=workflow_record,
                    step=step_name,
                    step_details=step_details,
                )

    async def _notify_workflow_started(
        self, workflow: WorkflowResource, workflow_record: WorkflowRecord
    ):
        results = await asyncio.gather(
            *[
                listener(
                    WorkflowStartEvent(
                        workflow=workflow, workflow_record=workflow_record
                    )
                )
                for listener in self.workflow_start_listeners
            ],
            return_exceptions=True,
        )
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.debug(
                    "(workflow-router) Exception while notifying workflow start listener %s: %s",
                    self.workflow_start_listeners[i],
                    result,
                )

    async def _notify_workflow_finished(
        self, workflow: WorkflowResource, workflow_record: WorkflowRecord
    ):
        results = await asyncio.gather(
            *[
                listener(
                    WorkflowFinishEvent(
                        workflow=workflow, workflow_record=workflow_record
                    )
                )
                for listener in self.workflow_finish_listeners
            ],
            return_exceptions=True,
        )
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.debug(
                    "(workflow-router) Exception while notifying workflow finish listener %s: %s",
                    self.workflow_finish_listeners[i],
                    result,
                )

    def add_workflow_start_listener(
        self, listener: Callable[[WorkflowStartEvent], Awaitable[None]]
    ):
        self.workflow_start_listeners.append(listener)

    def remove_workflow_start_listener(
        self, listener: Callable[[WorkflowStartEvent], Awaitable[None]]
    ):
        self.workflow_start_listeners.remove(listener)

    def add_workflow_finish_listener(
        self, listener: Callable[[WorkflowFinishEvent], Awaitable[None]]
    ):
        self.workflow_finish_listeners.append(listener)

    def remove_workflow_finish_listener(
        self, listener: Callable[[WorkflowFinishEvent], Awaitable[None]]
    ):
        self.workflow_finish_listeners.remove(listener)
