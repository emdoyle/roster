import json
from typing import Literal, Union

from pydantic import BaseModel, Field
from roster_api.resources.base import ResourceType


class PutResourceEvent(BaseModel):
    event_type: Literal["PUT"] = Field(default="PUT", description="The type of event.")
    resource_type: ResourceType = Field(description="The type of resource.")
    namespace: str = Field(
        default="default", description="The namespace of the resource."
    )
    name: str = Field(description="The name of the resource.")
    resource: dict = Field(description="The resource data itself.")
    spec_changed: bool = Field(
        default=False,
        description="Whether the spec of the resource has changed since the last event.",
    )
    status_changed: bool = Field(
        default=False,
        description="Whether the status of the resource has changed since the last event.",
    )

    class Config:
        use_enum_values = True
        validate_assignment = True

    def __str__(self):
        return f"({self.event_type} {self.resource_type} {self.namespace}/{self.name})"

    def serialize(self) -> bytes:
        return json.dumps(self.json()).encode("utf-8")


class DeleteResourceEvent(BaseModel):
    event_type: Literal["DELETE"] = Field(
        default="DELETE", description="The type of event."
    )
    resource_type: ResourceType = Field(description="The type of resource.")
    namespace: str = Field(default="default", description="The namespace of the agent.")
    name: str = Field(description="The name of the agent.")

    class Config:
        use_enum_values = True
        validate_assignment = True

    def __str__(self):
        return f"({self.event_type} {self.resource_type} {self.namespace}/{self.name})"

    def serialize(self) -> bytes:
        return json.dumps(self.json()).encode("utf-8")


ResourceEvent = Union[PutResourceEvent, DeleteResourceEvent]
