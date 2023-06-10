import logging
from typing import Callable, Optional

import pydantic
from roster_api import constants
from roster_api.events.resource import ResourceEvent
from roster_api.informers.base import Informer
from roster_api.models.task import TaskResource
from roster_api.resources.base import ResourceType
from roster_api.services.task import TaskService
from roster_api.watchers.resource import ResourceWatcher, get_resource_watcher

logger = logging.getLogger(constants.LOGGER_NAME)


class TaskInformer(Informer[TaskResource, ResourceEvent]):
    def __init__(self, resource_watcher: Optional[ResourceWatcher] = None):
        self.tasks: dict[str, TaskResource] = {}
        # This can be replaced with a listener on the HTTP event stream
        # if running separately from the API Server
        self.resource_watcher: ResourceWatcher = (
            resource_watcher or get_resource_watcher()
        )
        self.event_listeners: list[Callable[[ResourceEvent], None]] = []

    def _load_initial_tasks(self):
        tasks = TaskService().list_tasks()
        self.tasks = {task.spec.name: task for task in tasks}

    async def setup(self):
        logger.debug("Setting up Roster Informer")
        self._load_initial_tasks()
        self.resource_watcher.add_listener(self._handle_resource_event)

    async def teardown(self):
        logger.debug("Tearing down Roster Informer")
        self.resource_watcher.remove_listener(self._handle_resource_event)

    def _handle_put_resource_event(self, event: ResourceEvent) -> bool:
        if event.resource_type == ResourceType.Task:
            try:
                self.tasks[event.name] = TaskResource(**event.resource)
                return True
            except pydantic.ValidationError:
                logger.error("TaskInformer failed to parse TaskResource from event")
                logger.debug(
                    "(task-inf) Failed to parse TaskResource from event: %s",
                    event.resource,
                )
                return False
        else:
            logger.debug("(task-inf) Ignoring resource type: %s", event.resource_type)
            return False

    def _handle_delete_resource_event(self, event: ResourceEvent) -> bool:
        if event.resource_type == ResourceType.Task:
            self.tasks.pop(event.name, None)
            return True
        else:
            logger.debug("(task-inf) Ignoring resource type: %s", event.resource_type)
            return False

    def _handle_resource_event(self, event: ResourceEvent):
        logger.debug("(task-inf) Received Resource event: %s", event)
        if event.event_type == "PUT":
            handled = self._handle_put_resource_event(event)
        elif event.event_type == "DELETE":
            handled = self._handle_delete_resource_event(event)
        else:
            logger.warning("(task-inf) Unknown event: %s", event)
            return
        if not handled:
            logger.debug("(task-inf) Ignoring event: %s", event)
            return
        logger.debug("(task-inf) Pushing Resource event to listeners: %s", event)
        for listener in self.event_listeners:
            listener(event)

    def add_event_listener(self, callback: Callable[[ResourceEvent], None]):
        self.event_listeners.append(callback)

    def list_resources(self) -> list[TaskResource]:
        return list(self.tasks.values())

    def running_tasks_for_agent(
        self, name: str, namespace: str = "default"
    ) -> list[TaskResource]:
        return [
            task
            for task in self.tasks.values()
            if task.status.assignment is not None
            and task.status.assignment.agent_name == name
            and task.status.status != "done"  # TODO
        ]
