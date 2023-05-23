from typing import Optional

from pydantic import BaseModel, Field, constr
from roster_api.models.base import RosterResource


class AgentCapabilities(BaseModel):
    network_access: bool = Field(
        False, description="Whether the agent has network access or not."
    )
    messaging_access: bool = Field(
        False, description="Whether the agent can message other agents or not."
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "network_access": False,
                "messaging_access": False,
            },
        }


class AgentSpec(BaseModel):
    image: str = Field(description="The container image to be used for this agent.")
    name: str = Field(description="A name to identify the agent.")
    capabilities: AgentCapabilities = Field(
        default_factory=lambda: AgentCapabilities(),
        description="The capabilities of the agent.",
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "image": "my_image:latest",
                "name": "Alice",
                "capabilities": AgentCapabilities.Config.schema_extra["example"],
            }
        }


class AgentContainer(BaseModel):
    id: str = Field(description="The id of the container.")
    name: str = Field(
        max_length=128,
        regex=r"^/?[a-zA-Z0-9][a-zA-Z0-9_.-]+$",
        description="The name of the container.",
    )
    image: str = Field(description="The container image.")
    status: str = Field(description="The status of the container")
    labels: Optional[dict[str, str]] = Field(
        default=None, description="The labels of the container."
    )
    capabilities: AgentCapabilities = Field(
        description="The capabilities of the container."
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "id": "my_container_id",
                "image": "my_image:latest",
                "name": "my_container_name",
                "status": "running",
                "labels": {"my_label": "my_value"},
                "capabilities": AgentCapabilities.Config.schema_extra["example"],
            }
        }


class AgentStatus(BaseModel):
    name: str = Field(description="The name of the agent.")
    status: str = Field(default="pending", description="The status of the agent.")
    host_ip: str = Field(
        default="", description="The ip address of the host running the agent."
    )
    container: Optional[AgentContainer] = Field(
        default=None, description="The container running the agent."
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "name": "Alice",
                "status": "running",
                "host_ip": "127.0.0.1",
                "container": AgentContainer.Config.schema_extra["example"],
            }
        }


class AgentResource(RosterResource):
    kind: constr(regex="^Agent$") = Field(
        default="Agent", description="The kind of resource."
    )
    spec: AgentSpec = Field(description="The specification of the agent.")
    status: AgentStatus = Field(description="The status of the agent.")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "spec": AgentSpec.Config.schema_extra["example"],
                "status": AgentStatus.Config.schema_extra["example"],
            }
        }

    @classmethod
    def initial_state(cls, spec: AgentSpec) -> "AgentResource":
        return cls(spec=spec, status=AgentStatus(name=spec.name))
