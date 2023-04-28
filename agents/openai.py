from .base import AbstractAgent


class OpenAIAgent(AbstractAgent):
    def __init__(self, model: str):
        self.model = model

    @classmethod
    def from_resource(cls, agent_resource):
        return cls(agent_resource.backend.model)

    def assign_task(self, task_description):
        # Implement task assignment logic here
        print("OpenAI agent performing task: ", task_description)
        return "TODO"
