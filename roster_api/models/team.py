from pydantic import BaseModel, Field, constr
from roster_api import errors

from .base import RosterResource


class Role(BaseModel):
    description: str = Field(description="A description of the role.")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "description": "A description of the role.",
            }
        }


class Layout(BaseModel):
    roles: dict[str, Role] = Field(
        default_factory=dict, description="The roles in the layout."
    )
    peer_groups: dict[str, list[str]] = Field(
        default_factory=dict, description="The peer groups in the layout."
    )
    management_groups: dict[str, list[str]] = Field(
        default_factory=dict, description="The management groups in the layout."
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "roles": {
                    "role1": Role.Config.schema_extra["example"],
                    "role2": Role.Config.schema_extra["example"],
                },
                "peer_groups": {
                    "group1": ["role1", "role2"],
                    "group2": ["role2", "role3"],
                },
                "management_groups": {
                    "manager1": ["role1", "role2"],
                    "manager2": ["role3"],
                },
            }
        }

    @property
    def non_manager_roles(self) -> set[str]:
        return self.roles.keys() - self.management_groups.keys()


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


class TeamSpec(BaseModel):
    name: str = Field(description="A name to identify the team.")
    layout: Layout = Field(description="The layout of the team.")
    members: dict[str, Member] = Field(
        default_factory=dict, description="The members of the team."
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "name": "Red Team",
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

    def get_member(self, role: str) -> Member:
        try:
            return self.spec.members[role]
        except KeyError:
            raise errors.TeamMemberNotFoundError(member=role)
