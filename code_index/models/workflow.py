import logging
import uuid
from typing import ClassVar

from pydantic import BaseModel, Field, constr
from code_index import constants
from code_index.models.base import RosterResource
from code_index.models.common import TypedArgument, TypedResult
from code_index.util.graph_ops import sort_dependencies

logger = logging.getLogger(constants.LOGGER_NAME)


class StepRunConfig(BaseModel):
    num_retries: int = Field(
        default=0,
        description="The number of times to retry the Step if it fails.",
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "num_retries": 3,
            }
        }


class WorkflowStep(BaseModel):
    role: str = Field(description="The role that executes the action.")
    action: str = Field(description="The action to execute.")
    # TODO: field should be camelcase in JSON, but snakecase in Python
    inputMap: dict[str, str] = Field(
        default_factory=dict,
        description="Maps action inputs to available workflow values.",
    )
    outputMap: dict[str, str] = Field(
        default_factory=dict,
        description="Maps action outputs to workflow outputs. Only necessary for final actions.",
    )
    runConfig: StepRunConfig = Field(
        default_factory=StepRunConfig,
        description="The run configuration for the action.",
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "role": "WebDeveloper",
                "action": "CreatePullRequest",
                "inputMap": {"code": "Code.code"},
                "outputMap": {"pull_request": "workflow.feature_pull_request"},
                "runConfig": StepRunConfig.Config.schema_extra["example"],
            }
        }

    def get_dependencies(self) -> set[str]:
        deps = set()
        for dep_name in self.inputMap.values():
            # TODO: factor workflow variable namespacing into shared utility
            try:
                dep_step_name = dep_name.split(".")[0]
            except IndexError:
                raise ValueError(f"Could not parse step dependencies for step: {self}")
            if dep_step_name == "workflow":
                continue
            deps.add(dep_step_name)
        return deps


class WorkflowDerivedState(BaseModel):
    sorted_steps: list[str] = Field(
        default_factory=list, description="The sorted order of steps in the workflow."
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "sorted_steps": ["step1", "step2"],
            }
        }

    @classmethod
    def build(cls, spec: "WorkflowSpec") -> "WorkflowDerivedState":
        return cls(sorted_steps=sort_dependencies(spec.get_dependency_graph()))


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
    steps: dict[str, WorkflowStep] = Field(
        default_factory=dict, description="The steps in the workflow."
    )
    derived_state: WorkflowDerivedState = Field(
        default_factory=WorkflowDerivedState,
        description="The derived state from the workflow spec.",
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
                "steps": {
                    "step1": WorkflowStep.Config.schema_extra["example"],
                    "step2": WorkflowStep.Config.schema_extra["example"],
                },
                "derived_state": WorkflowDerivedState.Config.schema_extra["example"],
            }
        }

    def update_derived_state(self):
        self.derived_state = WorkflowDerivedState.build(spec=self)

    def get_dependency_graph(self) -> dict[str, set[str]]:
        workflow_graph = {}
        for step_name, step in self.steps.items():
            workflow_graph[step_name] = step.get_dependencies()
        return workflow_graph


class WorkflowStatus(BaseModel):
    name: str = Field(description="A name to identify the workflow.")
    status: str = Field(default="pending", description="The status of the workflow.")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "name": "WorkflowName",
                "status": "healthy",
            }
        }


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
                "kind": "Workflow",
                "spec": WorkflowSpec.Config.schema_extra["example"],
                "status": WorkflowStatus.Config.schema_extra["example"],
            }
        }

    @classmethod
    def initial_state(cls, spec: WorkflowSpec) -> "WorkflowResource":
        return cls(
            spec=spec,
            status=WorkflowStatus(name=spec.name),
        )


class InitiateWorkflowArgs(BaseModel):
    workflow: str = Field(description="The workflow to initiate.")
    inputs: dict[str, str] = Field(
        default_factory=dict, description="The inputs to the workflow."
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "workflow": "WorkflowName",
                "inputs": {"input1": "value1", "input2": "value2"},
            }
        }


class InitiateWorkflowPayload(BaseModel):
    KEY: ClassVar[str] = "initiate_workflow"
    inputs: dict[str, str] = Field(description="The inputs to the workflow.")
    workspace: str = Field(
        default="", description="The workspace in which the workflow is operating."
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "inputs": {"input1": "value1", "input2": "value2"},
                "workspace": "WorkspaceName",
            }
        }


class WorkflowActionReportPayload(BaseModel):
    KEY: ClassVar[str] = "report_action"
    step: str = Field(
        description="The name of the Step reporting outputs in this payload."
    )
    action: str = Field(description="The name of the Action which was run.")
    outputs: dict[str, TypedResult] = Field(
        default_factory=dict, description="The outputs of the Action being reported."
    )
    error: str = Field(
        default="",
        description="An error message if the Action failed to execute.",
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "step": "StepName",
                "action": "ActionName",
                "outputs": {
                    "output1": {"type": "text", "value": "value1"},
                    "output2": {"type": "text", "value": "value2"},
                },
                "error": "",
            }
        }


class WorkflowActionTriggerPayload(BaseModel):
    KEY: ClassVar[str] = "trigger_action"
    step: str = Field(
        description="The name of the Step reporting outputs in this payload."
    )
    action: str = Field(description="The name of the Action being triggered.")
    inputs: dict[str, str] = Field(
        description="The inputs for the Action being triggered."
    )
    role_context: str = Field(
        description="A description of the Role which is performing the Action."
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "step": "StepName",
                "action": "ActionName",
                "inputs": {"input1": "value1", "input2": "value2"},
                "role_context": "A description of the role",
            }
        }


WORKFLOW_MESSAGE_PAYLOADS = [
    InitiateWorkflowPayload,
    WorkflowActionReportPayload,
    WorkflowActionTriggerPayload,
]
MESSAGE_PAYLOADS_BY_KIND = {
    payload.KEY: payload for payload in WORKFLOW_MESSAGE_PAYLOADS
}


class WorkflowMessage(BaseModel):
    id: str = Field(
        description="An identifier for the workflow record this message refers to."
    )
    workflow: str = Field(description="The workflow this message refers to.")
    kind: str = Field(description="The kind of the message data.")
    data: dict = Field(default_factory=dict, description="The data of the message.")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "workflow": "WorkflowName",
                "kind": "initiate_workflow",
                "data": {
                    "inputs": {"input1": "value1", "input2": "value2"},
                },
            }
        }

    def read_contents(self):
        payload_cls = MESSAGE_PAYLOADS_BY_KIND.get(self.kind)
        if not payload_cls:
            # TODO: use constr or similar to avoid this on assignment
            raise ValueError(f"WorkflowMessage kind unknown: {self.kind}")

        return payload_cls.parse_obj(self.data)


class StepResult(BaseModel):
    outputs: dict[str, TypedResult] = Field(
        default_factory=dict,
        description="The outputs of the action run.",
    )
    error: str = Field(
        default="",
        description="An error message if the action failed to execute.",
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "outputs": {
                    "output1": {"type": "text", "value": "value1"},
                    "output2": {"type": "text", "value": "value2"},
                },
                "error": "",
            }
        }


class StepRunStatus(BaseModel):
    runs: int = Field(
        default=0,
        description="The number of times the step has been run.",
    )
    results: list[StepResult] = Field(
        default_factory=list,
        description="The results of the runs.",
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "runs": 0,
                "results": [
                    StepResult.Config.schema_extra["example"],
                    StepResult.Config.schema_extra["example"],
                ],
            }
        }


class WorkflowRecord(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="An identifier for the execution of the workflow.",
    )
    name: str = Field(description="The name of the workflow.")
    spec: WorkflowSpec = Field(
        description="The spec of the workflow at the time it was initiated."
    )
    workspace: str = Field(
        default="", description="The name of the associated workspace (if any)."
    )
    outputs: dict[str, TypedResult] = Field(
        default_factory=dict, description="The final outputs of the workflow."
    )
    errors: dict[str, str] = Field(
        default_factory=dict, description="The final errors of the workflow."
    )
    context: dict[str, TypedResult] = Field(
        default_factory=dict,
        description="The context (available values) of the workflow.",
    )
    run_status: dict[str, StepRunStatus] = Field(
        default_factory=dict,
        description="The run status of the actions in the workflow.",
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "WorkflowName",
                "spec": WorkflowSpec.Config.schema_extra["example"],
                "workspace": "my-branch-workspace",
                "outputs": {
                    "output1": {"type": "text", "value": "value1"},
                    "output2": {"type": "text", "value": "value2"},
                },
                "error": "",
                "context": {
                    "ctx1": {"type": "text", "value": "value1"},
                    "ctx2": {"type": "text", "value": "value2"},
                },
                "run_status": {
                    "ActionName": StepRunStatus.Config.schema_extra["example"],
                },
            }
        }


# TODO: narrow these to specific fields?
class WorkflowStartEvent(BaseModel):
    workflow_record: WorkflowRecord


class WorkflowFinishEvent(BaseModel):
    workflow_record: WorkflowRecord
