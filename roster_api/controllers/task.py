import asyncio
import logging
from typing import Optional

import pydantic
from roster_api import constants, errors
from roster_api.events.resource import ResourceEvent
from roster_api.executors.task import TaskExecutor
from roster_api.informers.task import TaskInformer
from roster_api.models.task import TaskResource, TaskStatus
from roster_api.resources.base import ResourceType
from roster_api.services.task import TaskService

logger = logging.getLogger(constants.LOGGER_NAME)


# This Controller deviates a bit from a typical Controller:
# - no direct connection to volatile state
#   (state is derived from the TaskInformer cache,
#    which comes from Roster event stream)
#   TODO: this means Task DELETEs and otherwise orphaned Tasks
#     can't easily be detected
# - shared responsibility for status updates
#   (Agents themselves send some status updates)
# - no reconcile loop since Tasks are independent
#   (reconcile each separately)
class TaskController:
    def __init__(
        self,
        task_executor: TaskExecutor,
        task_informer: TaskInformer,
        task_service: Optional[TaskService] = None,
    ):
        # TaskExecutor is used to issue commands during reconciliation
        self.task_executor = task_executor
        # TaskInformer maintains a local cache of Task resources
        #   and emits events on relevant Task, Agent resource changes
        self.task_informer = task_informer
        # TaskService only used for pushing status changes to etcd
        #   analogous to RosterNotifier
        self.task_service = task_service or TaskService()

    async def setup(self):
        logger.debug("(task-control) Setup started.")
        try:
            await self.task_informer.setup()
            logger.debug(
                "(task-control) Initial setup complete. Starting reconciliation..."
            )
            await self.reconcile()
            self.task_informer.add_event_listener(self._handle_resource_event)
        except Exception as e:
            await self.teardown()
            raise errors.SetupError from e
        logger.debug("(task-control) Setup complete.")

    async def teardown(self):
        logger.debug("(task-control) Teardown started.")
        try:
            await self.task_informer.teardown()
        except Exception as e:
            raise errors.TeardownError from e
        logger.debug("(task-control) Teardown complete.")

    async def _reconcile_task(self, task: TaskResource):
        logger.debug("(task-control) Reconciling task %s", task.spec.name)
        if task.status.assignment is None:
            try:
                assignment = await self.task_executor.assign_task(task.spec)
            except errors.RosterAPIError as e:
                logger.error("Failed to assign task %s", task.spec.name)
                logger.debug(
                    "(task-control) Failed to assign task %s, Error: %s",
                    task.spec.name,
                    e,
                )
                return
            # Update etcd with assignment
            # TaskInformer cache will be updated automatically by event stream,
            # and subsequent reconciliation will be a no-op.
            self.task_service.update_task_status(
                TaskStatus(**task.status.dict(), assignment=assignment)
            )
        logger.debug("(task-control) Reconciled task %s", task.spec.name)

    async def reconcile(self):
        logger.info("TaskController reconciling...")
        logger.debug("(task-control) Reconciling tasks...")
        task_resources = self.task_informer.list_resources()
        try:
            await asyncio.gather(
                *[
                    self._reconcile_task(task_resource)
                    for task_resource in task_resources
                ]
            )
        except Exception as e:
            logger.error("TaskController failed to reconcile tasks.")
            logger.debug(
                "(task-control) TaskController failed to reconcile tasks. Error: %s",
                e,
            )
            return
        logger.debug("(task-control) Reconciled tasks.")
        logger.info("TaskController reconciled.")

    def _handle_resource_event(self, event: ResourceEvent):
        if event.event_type == "DELETE":
            if event.resource_type == ResourceType.Task:
                self._cancel_task(event.name, event.namespace)
            elif event.resource_type == ResourceType.Agent:
                self._handle_agent_deleted(event.name, event.namespace)
        elif event.event_type == "PUT" and event.resource_type == ResourceType.Task:
            try:
                task_resource = TaskResource(**event.resource)
            except pydantic.ValidationError:
                logger.error("TaskController could not parse Task resource from event")
                logger.debug(
                    "TaskController could not parse Task resource from event: %s",
                    event.resource,
                )
                return
            # This is running from WITHIN the ResourceWatcher,
            # which is a separate Thread.
            asyncio.run(self._reconcile_task(task=task_resource))
        else:
            logger.warning(
                "TaskController received unexpected Resource event: %s", event
            )

    def _cancel_task(self, task_name: str, namespace: str = "default"):
        logger.debug("(task-control) Cancelling Task %s (%s)", task_name, namespace)
        try:
            # This is running from WITHIN the ResourceWatcher,
            # which is a separate Thread.
            asyncio.run(
                self.task_executor.cancel_task(name=task_name, namespace=namespace)
            )
        except errors.RosterAPIError as e:
            logger.error("Failed to cancel task %s", task_name)
            logger.debug(
                "(task-control) Failed to cancel task %s, Error: %s",
                task_name,
                e,
            )
            return

    def _handle_agent_deleted(self, agent_name: str, namespace: str = "default"):
        logger.debug(
            "(task-control) Handling deleted Agent %s (%s)", agent_name, namespace
        )
        agent_tasks = self.task_informer.running_tasks_for_agent(
            name=agent_name, namespace=namespace
        )
        if not agent_tasks:
            return
        logger.debug(
            "(task-control) Found running tasks on deleted Agent, clearing assignment status."
        )
        for task in agent_tasks:
            # Update etcd with assignment=None
            # This will result in re-assignment via reconciliation
            logger.debug(
                "(task-control) Clearing assignment for Task %s (%s)",
                task.spec.name,
                namespace,
            )
            self.task_service.update_task_status(
                TaskStatus(**task.status.dict(), assignment=None)
            )
