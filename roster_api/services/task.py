import logging
from typing import Optional

import etcd3
import pydantic
from roster_api import constants, errors
from roster_api.db.etcd import get_etcd_client
from roster_api.events.status import StatusEvent
from roster_api.models.task import TaskResource, TaskSpec, TaskStatus

logger = logging.getLogger(constants.LOGGER_NAME)


class TaskService:
    KEY_PREFIX = "/registry/tasks"
    DEFAULT_NAMESPACE = "default"

    def __init__(self, etcd_client: Optional[etcd3.Etcd3Client] = None):
        self.etcd_client: etcd3.Etcd3Client = etcd_client or get_etcd_client()

    def _get_task_key(self, task_name: str, namespace: str = DEFAULT_NAMESPACE) -> str:
        return f"{self.KEY_PREFIX}/{namespace}/{task_name}"

    def create_task(
        self, task: TaskSpec, namespace: str = DEFAULT_NAMESPACE
    ) -> TaskResource:
        task_key = self._get_task_key(task.name, namespace)
        task_resource = TaskResource.initial_state(spec=task)
        created = self.etcd_client.put_if_not_exists(
            task_key, task_resource.serialize()
        )
        if not created:
            raise errors.TaskAlreadyExistsError(task=task)
        logger.debug("Created Task %s", task.name)
        return task_resource

    def get_task(self, name: str, namespace: str = DEFAULT_NAMESPACE) -> TaskResource:
        task_key = self._get_task_key(name, namespace)
        task_data, _ = self.etcd_client.get(task_key)
        if not task_data:
            raise errors.TaskNotFoundError(task=name)
        return TaskResource.deserialize_from_etcd(task_data)

    def list_tasks(self, namespace: str = DEFAULT_NAMESPACE) -> list[TaskResource]:
        task_key = self._get_task_key("", namespace)
        task_data = self.etcd_client.get_prefix(task_key)
        return [TaskResource.deserialize_from_etcd(data) for data, _ in task_data]

    def update_task(
        self, task: TaskSpec, namespace: str = DEFAULT_NAMESPACE
    ) -> TaskResource:
        task_key = self._get_task_key(task.name, namespace)
        task_resource = self.get_task(task.name, namespace)
        task_resource.spec = task
        self.etcd_client.put(task_key, task_resource.serialize())
        logger.debug(f"Updated Task {task.name}.")
        return task_resource

    def delete_task(self, name: str, namespace: str = DEFAULT_NAMESPACE) -> bool:
        task_key = self._get_task_key(name, namespace)
        deleted = self.etcd_client.delete(task_key)
        if deleted:
            logger.debug(f"Deleted Task {name}.")
        return deleted

    def _handle_task_status_put(self, status_update: StatusEvent):
        task_key = self._get_task_key(status_update.name)
        task_data, _ = self.etcd_client.get(task_key)
        if not task_data:
            raise errors.TaskNotFoundError(task=status_update.name)
        try:
            updated_status = TaskStatus(**status_update.status)
        except pydantic.ValidationError as e:
            raise errors.InvalidEventError(event=status_update) from e
        task_resource = TaskResource.deserialize_from_etcd(task_data)
        task_resource.status = updated_status
        self.etcd_client.put(task_key, task_resource.serialize())
        logger.debug("Updated Task %s status.", status_update.name)

    def _handle_task_status_delete(self, status_update: StatusEvent):
        task_key = self._get_task_key(status_update.name)
        task_data, _ = self.etcd_client.get(task_key)
        if not task_data:
            logger.debug("Task %s already deleted.", status_update.name)
            return
        task_resource = TaskResource.deserialize_from_etcd(task_data)
        task_resource.status = TaskStatus(name=status_update.name, status="deleted")
        self.etcd_client.put(task_key, task_resource.serialize())
        logger.debug("Deleted Task %s status.", status_update.name)

    def handle_task_status_update(self, status_update: StatusEvent):
        if status_update.event_type == "PUT":
            self._handle_task_status_put(status_update)
        elif status_update.event_type == "DELETE":
            self._handle_task_status_delete(status_update)
        else:
            logger.warning(
                "Received status update for unknown event type: %s",
                status_update.event_type,
            )
