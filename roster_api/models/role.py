from typing import Optional

from pydantic import BaseModel, Field, constr
from roster_api.models.base import RosterResource


class RoleSpec(BaseModel):
    name: str = Field(description="A name to identify the role.")
    description: str = Field(description="A description of the role.")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "name": "Role Manager",
                "description": "A description of the role.",
            }
        }


class RoleStatus(BaseModel):
    name: str = Field(description="A name to identify the role.")
    status: str = Field(default="active", description="The status of the role.")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "name": "Role Manager",
                "status": "active",
            }
        }


class RoleResource(RosterResource):
    kind: constr(regex="^Role$") = Field(
        default="Role", description="The kind of resource."
    )
    spec: RoleSpec = Field(description="The specification of the role.")
    status: RoleStatus = Field(description="The status of the role.")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "spec": RoleSpec.Config.schema_extra["example"],
                "status": RoleStatus.Config.schema_extra["example"],
            }
        }

    @classmethod
    def initial_state(cls, spec: RoleSpec) -> "RoleResource":
        return cls(spec=spec, status=RoleStatus(name=spec.name))
