from abc import abstractmethod


class AbstractAgent:
    @classmethod
    @abstractmethod
    def from_resource(cls, agent_resource: "resources.Agent"):
        pass

    @abstractmethod
    def assign_task(self, task_description: str) -> str:
        pass
