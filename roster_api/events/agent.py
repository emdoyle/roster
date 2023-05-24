import json
from typing import Union

from pydantic import BaseModel, Field
from roster_api.models.agent import AgentSpec


class PutAgentSpecEvent(BaseModel):
    namespace: str = Field(description="The namespace of the agent.")
    name: str = Field(description="The name of the agent.")
    spec: AgentSpec = Field(description="The specification of the agent.")

    class Config:
        validate_assignment = True

    def __str__(self):
        return f"(PUT {self.namespace}/{self.name})"

    def serialize(self) -> bytes:
        return json.dumps(self.json()).encode("utf-8")

    @classmethod
    def deserialize(cls, data: bytes) -> "PutAgentSpecEvent":
        return cls.parse_raw(data.decode("utf-8"))


class DeleteAgentSpecEvent(BaseModel):
    namespace: str = Field(description="The namespace of the agent.")
    name: str = Field(description="The name of the agent.")

    class Config:
        validate_assignment = True

    def __str__(self):
        return f"(DELETE {self.namespace}/{self.name})"

    def serialize(self) -> bytes:
        return json.dumps(self.json()).encode("utf-8")

    @classmethod
    def deserialize(cls, data: bytes) -> "DeleteAgentSpecEvent":
        return cls.parse_raw(data.decode("utf-8"))


AgentSpecEvent = Union[PutAgentSpecEvent, DeleteAgentSpecEvent]
