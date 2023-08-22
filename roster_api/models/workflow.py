from pydantic import BaseModel, Field, constr
from roster_api.models.base import RosterResource
from roster_api.models.common import TypedArgument


class WorkflowAction(BaseModel):
    role: str = Field(description="The role that executes the action.")
    action: str = Field(description="The action to execute.")
    inputMap: dict[str, str] = Field(
        default_factory=dict,
        description="Maps action inputs to available workflow values.",
    )
    outputMap: dict[str, str] = Field(
        default_factory=dict,
        description="Maps action outputs to workflow outputs. Only necessary for final actions.",
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "role": "WebDeveloper",
                "action": "CreatePullRequest",
                "inputMap": {"code": "Code.code"},
                "outputMap": {"pull_request": "workflow.feature_pull_request"},
            }
        }


class WorkflowSpec(BaseModel):
    name: str = Field(description="A name to identify the workflow.")
    description: str = Field(description="A description of the workflow.")
    team: str = Field(description="The team that executes the workflow.")
    inputs: list[TypedArgument] = Field(
        default_factory=list, description="The inputs to the workflow."
    )
    outputs: list[TypedArgument] = Field(
        default_factory=list, description="The outputs of the workflow."
    )
    actions: dict[str, WorkflowAction] = Field(
        default_factory=dict, description="The actions of the workflow."
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "name": "WorkflowName",
                "description": "A description of the workflow.",
                "team": "TeamName",
                "inputs": [
                    TypedArgument.Config.schema_extra["example"],
                    TypedArgument.Config.schema_extra["example"],
                ],
                "outputs": [
                    TypedArgument.Config.schema_extra["example"],
                    TypedArgument.Config.schema_extra["example"],
                ],
                "actions": {
                    "action1": WorkflowAction.Config.schema_extra["example"],
                    "action2": WorkflowAction.Config.schema_extra["example"],
                },
            }
        }


class WorkflowStatus(BaseModel):
    name: str = Field(description="A name to identify the workflow.")
    status: str = Field(description="The status of the workflow.")


class WorkflowResource(RosterResource):
    kind: constr(regex="^Workflow$") = Field(
        default="Workflow", description="The kind of resource."
    )
    spec: WorkflowSpec = Field(description="The specification of the workflow.")
    status: WorkflowStatus = Field(description="The status of the workflow.")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "spec": WorkflowSpec.Config.schema_extra["example"],
                "status": WorkflowStatus.Config.schema_extra["example"],
            }
        }

    @classmethod
    def initial_state(cls, spec: WorkflowSpec) -> "WorkflowResource":
        return cls(spec=spec, status=WorkflowStatus(name=spec.name))
