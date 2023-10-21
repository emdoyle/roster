from pydantic import BaseModel, Field, constr
from code_index.models.base import RosterResource


class IdentitySpec(BaseModel):
    name: str = Field(description="A name to identify the identity.")
    description: str = Field(description="A description of the identity.")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "name": "Charlie",
                "description": "A description of the identity.",
            }
        }


class IdentityStatus(BaseModel):
    name: str = Field(description="A name to identify the identity.")
    status: str = Field(default="active", description="The status of the identity.")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "name": "Charlie",
                "status": "active",
            }
        }


class IdentityResource(RosterResource):
    kind: constr(regex="^Identity$") = Field(
        default="Identity", description="The kind of resource."
    )
    spec: IdentitySpec = Field(description="The specification of the identity.")
    status: IdentityStatus = Field(description="The status of the identity.")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "spec": IdentitySpec.Config.schema_extra["example"],
                "status": IdentityStatus.Config.schema_extra["example"],
            }
        }

    @classmethod
    def initial_state(cls, spec: IdentitySpec) -> "IdentityResource":
        return cls(spec=spec, status=IdentityStatus(name=spec.name))
