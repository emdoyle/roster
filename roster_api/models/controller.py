from pydantic import BaseModel, Field

from .task import TaskResource, TaskSpec, TaskStatus


# Not using this right now,
# but it is necessary for TaskController
# once it actually watches volatile TaskStatus
class TaskControllerStore(BaseModel):
    desired: list[TaskSpec] = Field(
        default_factory=list,
        description="The list of tasks which should be running.",
    )
    current: list[TaskStatus] = Field(
        default_factory=list,
        description="The list of tasks which are currently running.",
    )

    def reinitialize_from_resources(self, resources: list[TaskResource]):
        self.desired = []
        self.current = []
        for task_resource in resources:
            self.desired.append(task_resource.spec)
            self.current.append(task_resource.status)

    def current_tasks_for_agent(self, agent_name: str) -> list[TaskStatus]:
        return [
            task
            for task in self.current
            if task.assignment is not None and task.assignment.agent_name == agent_name
        ]
