import json
from typing import Literal, Union

from pydantic import BaseModel, Field


class PutSpecEvent(BaseModel):
    event_type: Literal["PUT"] = Field(default="PUT", description="The type of event.")
    resource_type: str = Field(description="The type of resource.")
    namespace: str = Field(
        default="default", description="The namespace of the resource."
    )
    name: str = Field(description="The name of the resource.")
    spec: dict = Field(description="The specification of the resource.")

    class Config:
        validate_assignment = True

    def __str__(self):
        return f"({self.event_type} {self.resource_type} {self.namespace}/{self.name})"

    def serialize(self) -> bytes:
        return json.dumps(self.json()).encode("utf-8")


class DeleteSpecEvent(BaseModel):
    event_type: Literal["DELETE"] = Field(
        default="DELETE", description="The type of event."
    )
    resource_type: str = Field(description="The type of resource.")
    namespace: str = Field(default="default", description="The namespace of the agent.")
    name: str = Field(description="The name of the agent.")

    class Config:
        validate_assignment = True

    def __str__(self):
        return f"({self.event_type} {self.resource_type} {self.namespace}/{self.name})"

    def serialize(self) -> bytes:
        return json.dumps(self.json()).encode("utf-8")


SpecEvent = Union[PutSpecEvent, DeleteSpecEvent]
