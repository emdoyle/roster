from typing import Optional

from pydantic import BaseModel, Field
from roster_api.models.outputs import CodeOutput


class WorkflowCodeReportPayload(BaseModel):
    workflow_name: str = Field(description="Name of the workflow which was run")
    workflow_record: str = Field(description="ID of the workflow record")
    code_outputs: list[CodeOutput] = Field(
        default_factory=list,
        description="The outputs of the workflow record with type 'code'",
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "workflow_name": "my-workflow",
                "workflow_record": "1234",
            }
        }


class WorkspaceMessage(BaseModel):
    workspace: str = Field(
        description="The name of the Workspace associated with this message"
    )
    namespace: str = Field(
        default="default",
        description="The namespace of the Workspace associated with this message",
    )
    kind: str = Field(description="The kind of the message data")
    data: dict = Field(default_factory=dict, description="The data of the message")

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "workspace": "my-workspace",
                "namespace": "default",
                "kind": "workflow_code_report",
                "data": WorkflowCodeReportPayload.Config.schema_extra["example"],
            }
        }


class GithubWorkspace(BaseModel):
    installation_id: int = Field(
        description="The installation ID for the Github App Installation"
    )
    repository_name: str = Field(
        description="The name of the repository which is being worked on"
    )
    branch_name: str = Field(
        description="The name of the branch which is being worked on"
    )
    base_hash: str = Field(
        description="The hash of the base commit for the branch which is being worked on"
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "installation_id": "1234",
                "repository_name": "my-org/my-repo",
                "branch_name": "my-branch",
                "base_hash": "1234567890abcdef",
            }
        }


class Workspace(BaseModel):
    name: str = Field(description="The name of the workspace")
    kind: str = Field(description="The kind of workspace")
    github_info: Optional[GithubWorkspace] = Field(
        default=None, description="The details of a github workspace"
    )

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "name": "my-workspace",
                "kind": "github",
                "github_info": GithubWorkspace.Config.schema_extra["example"],
            }
        }
