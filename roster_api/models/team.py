from pydantic import BaseModel, Field, constr
from roster_api import errors

from .base import RosterResource
from .common import TypedArgument


class Role(BaseModel):
    name: str = Field(description="A name to identify the role.")
    description: str = Field(description="A description of the role.")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "name": "RoleName",
                "description": "A description of the role.",
            }
        }


class Layout(BaseModel):
    roles: list[Role] = Field(
        default_factory=list, description="The roles in the layout."
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "roles": [
                    Role.Config.schema_extra["example"],
                    Role.Config.schema_extra["example"],
                ]
            }
        }


class Member(BaseModel):
    identity: str = Field(description="The identity of the member.")
    agent: str = Field(description="The agent running this member.")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "identity": "Alice",
                "agent": "agent1",
            }
        }


class Workflow(BaseModel):
    name: str = Field(description="A name to identify the workflow.")
    inputs: list[TypedArgument] = Field(
        default_factory=list, description="The inputs to the workflow."
    )
    outputs: list[TypedArgument] = Field(
        default_factory=list, description="The outputs of the workflow."
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "name": "WorkflowName",
                "inputs": [
                    TypedArgument.Config.schema_extra["example"],
                    TypedArgument.Config.schema_extra["example"],
                ],
                "outputs": [
                    TypedArgument.Config.schema_extra["example"],
                    TypedArgument.Config.schema_extra["example"],
                ],
            }
        }


class TeamSpec(BaseModel):
    name: str = Field(description="A name to identify the team.")
    type: str = Field(description="The type of the team.")
    description: str = Field(
        description="A description of the team and its capabilities."
    )
    layout: Layout = Field(description="The layout of the team.")
    workflows: list[Workflow] = Field(
        default_factory=list, description="The workflows which the team implements."
    )
    members: dict[str, Member] = Field(
        default_factory=dict, description="The members of the team."
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "name": "Red Team",
                "type": "red",
                "description": "A description of the team and its capabilities.",
                "layout": Layout.Config.schema_extra["example"],
                "members": {
                    "member1": Member.Config.schema_extra["example"],
                    "member2": Member.Config.schema_extra["example"],
                },
            }
        }


class TeamStatus(BaseModel):
    name: str = Field(description="A name to identify the team.")
    status: str = Field(default="active", description="The status of the team.")
    members: dict[str, Member] = Field(
        default_factory=dict, description="The members of the team."
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "name": "Red Team",
                "status": "active",
                "members": {
                    "member1": Member.Config.schema_extra["example"],
                    "member2": Member.Config.schema_extra["example"],
                },
            }
        }


class TeamResource(RosterResource):
    kind: constr(regex="^Team$") = Field(
        default="Team", description="The kind of resource."
    )
    spec: TeamSpec = Field(description="The specification of the team.")
    status: TeamStatus = Field(description="The status of the team.")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "spec": TeamSpec.Config.schema_extra["example"],
                "status": TeamStatus.Config.schema_extra["example"],
            }
        }

    @classmethod
    def initial_state(cls, spec: TeamSpec) -> "TeamResource":
        return cls(spec=spec, status=TeamStatus(name=spec.name))

    def get_member(self, role: str) -> Member:
        try:
            return self.status.members[role]
        except KeyError:
            raise errors.TeamMemberNotFoundError(member=role)
