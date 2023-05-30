from pydantic import BaseModel, Field, constr

from .base import RosterResource
from .role import RoleSpec


class TeamLayoutSpec(BaseModel):
    name: str = Field(description="A name to identify the team layout.")
    roles: dict[str, RoleSpec] = Field(
        default_factory=dict, description="The roles of the team layout."
    )
    peer_groups: dict[str, list[str]] = Field(
        default_factory=dict, description="The peer groups of the team layout."
    )
    management_groups: dict[str, list[str]] = Field(
        default_factory=dict, description="The management groups of the team layout."
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "name": "Red TeamLayout",
                "roles": {
                    "role1": RoleSpec.Config.schema_extra["example"],
                    "role2": RoleSpec.Config.schema_extra["example"],
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


class TeamLayoutStatus(BaseModel):
    name: str = Field(description="A name to identify the team layout.")
    status: str = Field(default="active", description="The status of the team layout.")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "name": "Red TeamLayout",
                "status": "active",
            }
        }


class TeamLayoutResource(RosterResource):
    kind: constr(regex="^TeamLayout$") = Field(
        default="TeamLayout", description="The kind of resource."
    )
    spec: TeamLayoutSpec = Field(description="The specification of the team layout.")
    status: TeamLayoutStatus = Field(description="The status of the team layout.")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "spec": TeamLayoutSpec.Config.schema_extra["example"],
                "status": TeamLayoutStatus.Config.schema_extra["example"],
            }
        }

    @classmethod
    def initial_state(cls, spec: TeamLayoutSpec) -> "TeamLayoutResource":
        return cls(spec=spec, status=TeamLayoutStatus(name=spec.name))
