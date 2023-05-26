from pydantic import BaseModel, Field, constr

from .agent import AgentSpec
from .base import RosterResource
from .team_layout import TeamLayoutSpec


class TeamSpec(BaseModel):
    name: str = Field(description="A name to identify the team.")
    layout: TeamLayoutSpec = Field(description="The layout of the team.")
    members: dict[str, AgentSpec] = Field(
        default_factory=list, description="The members of the team."
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "name": "Red Team",
                "layout": TeamLayoutSpec.Config.schema_extra["example"],
                "members": {
                    "agent1": AgentSpec.Config.schema_extra["example"],
                    "agent2": AgentSpec.Config.schema_extra["example"],
                },
            }
        }


class TeamStatus(BaseModel):
    name: str = Field(description="A name to identify the team.")
    status: str = Field(default="active", description="The status of the team.")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "name": "Red Team",
                "status": "active",
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
