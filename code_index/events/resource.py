from typing import Literal, Optional, Union

from pydantic import BaseModel, Field
from code_index.resources.base import ResourceType


class PutResourceEvent(BaseModel):
    event_type: Literal["PUT"] = Field(default="PUT", description="The type of event.")
    resource_type: ResourceType = Field(description="The type of resource.")
    namespace: str = Field(
        default="default", description="The namespace of the resource."
    )
    name: str = Field(description="The name of the resource.")
    resource: dict = Field(description="The resource data itself.")
    previous_resource: Optional[dict] = Field(
        default=None, description="The previous resource data, when available."
    )
    spec_changed: bool = Field(
        default=False,
        description="Whether the spec of the resource has changed since the last event.",
    )
    status_changed: bool = Field(
        default=False,
        description="Whether the status of the resource has changed since the last event.",
    )

    class Config:
        validate_assignment = True

    def __str__(self):
        return f"({self.event_type} {self.resource_type.value} {self.namespace}/{self.name})"


class DeleteResourceEvent(BaseModel):
    event_type: Literal["DELETE"] = Field(
        default="DELETE", description="The type of event."
    )
    resource_type: ResourceType = Field(description="The type of resource.")
    namespace: str = Field(
        default="default", description="The namespace of the resource."
    )
    name: str = Field(description="The name of the resource.")
    resource: dict = Field(description="The (deleted) resource data itself.")

    class Config:
        validate_assignment = True

    def __str__(self):
        return f"({self.event_type} {self.resource_type.value} {self.namespace}/{self.name})"


ResourceEvent = Union[PutResourceEvent, DeleteResourceEvent]
