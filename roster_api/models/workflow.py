import json
import logging
import uuid
from typing import ClassVar

import pydantic
from pydantic import BaseModel, Field, constr
from roster_api import constants, errors
from roster_api.models.base import RosterResource
from roster_api.models.common import TypedArgument

logger = logging.getLogger(constants.LOGGER_NAME)


class ActionRunConfig(BaseModel):
    num_retries: int = Field(
        default=0,
        description="The number of times to retry the action if it fails.",
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "num_retries": 3,
            }
        }


class WorkflowAction(BaseModel):
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
    runConfig: ActionRunConfig = Field(
        default_factory=ActionRunConfig,
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
                "runConfig": ActionRunConfig.Config.schema_extra["example"],
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
                "spec": WorkflowSpec.Config.schema_extra["example"],
                "status": WorkflowStatus.Config.schema_extra["example"],
            }
        }

    @classmethod
    def initial_state(cls, spec: WorkflowSpec) -> "WorkflowResource":
        return cls(spec=spec, status=WorkflowStatus(name=spec.name))


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

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "inputs": {"input1": "value1", "input2": "value2"},
            }
        }


class WorkflowActionReportPayload(BaseModel):
    KEY: ClassVar[str] = "report_action"
    action: str = Field(
        description="The name of the Action reporting outputs in this payload."
    )
    outputs: dict[str, str] = Field(
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
                "action": "ActionName",
                "outputs": {"output1": "value1", "output2": "value2"},
                "error": "",
            }
        }


class WorkflowActionTriggerPayload(BaseModel):
    KEY: ClassVar[str] = "trigger_action"
    action: str = Field(
        description="The name of the Action reporting outputs in this payload."
    )
    inputs: dict[str, str] = Field(
        description="The inputs for the Action being triggered."
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "action": "ActionName",
                "inputs": {"input1": "value1", "input2": "value2"},
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


class ActionResult(BaseModel):
    outputs: dict[str, str] = Field(
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
                "outputs": {"output1": "value1", "output2": "value2"},
                "error": "",
            }
        }


class ActionRunStatus(BaseModel):
    runs: int = Field(
        default=0,
        description="The number of times the action has been run.",
    )
    results: list[ActionResult] = Field(
        default_factory=list,
        description="The results of the action runs.",
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "runs": 0,
                "results": [
                    ActionResult.Config.schema_extra["example"],
                    ActionResult.Config.schema_extra["example"],
                ],
            }
        }


class WorkflowRecord(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="An identifier for the execution of the workflow.",
    )
    name: str = Field(description="The name of the workflow.")
    context: dict[str, str] = Field(
        default_factory=dict,
        description="The context (available values) of the workflow.",
    )
    run_status: dict[str, ActionRunStatus] = Field(
        default_factory=dict,
        description="The run status of the actions in the workflow.",
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "WorkflowName",
                "context": {"input1": "value1", "input2": "value2"},
                "run_status": {
                    "ActionName": ActionRunStatus.Config.schema_extra["example"],
                },
            }
        }

    # TODO: consider sharing ser/deser with RosterResource
    def serialize(self) -> bytes:
        return json.dumps(self.json()).encode("utf-8")

    @classmethod
    def deserialize_from_etcd(cls, data: bytes) -> "WorkflowRecord":
        try:
            # SSE data is double-encoded
            return cls(**json.loads(json.loads(data.decode("utf-8"))))
        except (
            pydantic.ValidationError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as e:
            logger.error(
                "Failed to deserialize data from etcd for class: %s", cls.__name__
            )
            raise errors.InvalidResourceError(
                "Could not deserialize resource from etcd."
            ) from e
