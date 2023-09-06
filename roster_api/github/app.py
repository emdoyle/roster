import json
import logging
from typing import Optional

from roster_api import constants
from roster_api.messaging.workflow import WorkflowRouter
from roster_api.models.outputs import CodeOutput
from roster_api.models.workflow import WorkflowFinishEvent
from roster_api.models.workspace import (
    GithubWorkspace,
    WorkflowCodeReportPayload,
    Workspace,
    WorkspaceMessage,
)
from roster_api.services.workflow import WorkflowService
from roster_api.services.workspace import WorkspaceService
from roster_api.singletons import get_workflow_router, get_workspace_manager
from roster_api.workspace.manager import WorkspaceManager

from .service import GithubService

logger = logging.getLogger(constants.LOGGER_NAME)


class RosterGithubApp:
    def __init__(
        self,
        workflow_router: Optional[WorkflowRouter] = None,
        workspace_manager: Optional[WorkspaceManager] = None,
    ):
        self.workflow_router = workflow_router or get_workflow_router()
        self.workspace_manager = workspace_manager or get_workspace_manager()

    async def setup(self):
        self.workflow_router.add_workflow_finish_listener(self.handle_workflow_finish)

    async def teardown(self):
        self.workflow_router.remove_workflow_finish_listener(
            self.handle_workflow_finish
        )

    async def handle_webhook_payload(self, payload: dict):
        github_service = GithubService.from_webhook_payload(payload=payload)

        if "issue" in payload and payload["action"] in [
            "opened",
            "reopened",
        ]:
            await self.handle_issue_created(
                github_service=github_service, payload=payload
            )

        elif "issue" in payload and "comment" in payload:
            await self.handle_issue_comment(
                github_service=github_service, payload=payload
            )
        else:
            logger.debug("(roster-gha) Unrecognized payload: %s", payload)

    async def handle_issue_created(self, github_service: GithubService, payload: dict):
        try:
            issue_title = payload["issue"]["title"]
            issue_number = payload["issue"]["number"]
            issue_body = payload["issue"]["body"]
        except KeyError:
            logger.error("(roster-gha) Failed to parse issue title from payload")
            return

        workspace = Workspace(
            name=f"issue-{issue_number}",
            kind="github",
            github_info=GithubWorkspace(
                installation_id=github_service.installation_id,
                repository_name=github_service.repository_name,
                branch_name=f"issue-{issue_number}",
            ),
        )
        WorkspaceService().update_or_create_workspace(workspace=workspace)
        await WorkflowService().initiate_workflow(
            workflow_name="ImplementFeature",  # TODO: make this configurable
            inputs={
                "feature_description": f"Title: {issue_title}\n\nRequest:\n{issue_body}",
                "codebase_tree": self.workspace_manager.build_codebase_tree(
                    github_service=github_service
                ),
            },
            workspace_name=workspace.name,
        )
        await github_service.handle_issue_created(payload=payload)

    async def handle_issue_comment(self, github_service: GithubService, payload: dict):
        await github_service.handle_issue_comment(payload=payload)

    # NOTE: probably makes sense to push the finish event handling logic
    #   into the WorkspaceManager
    async def handle_workflow_finish(self, event: WorkflowFinishEvent):
        workspace_service = WorkspaceService()
        if not event.workflow_record.workspace:
            logger.debug(
                "(roster-gha) Workflow record has no workspace: %s",
                event.workflow_record.id,
            )
            return
        workspace = workspace_service.get_workspace(event.workflow_record.workspace)
        workflow_outputs = event.workflow.spec.outputs

        code_output_keys = [
            output.name for output in workflow_outputs if output.type == "code"
        ]
        code_outputs = []
        for code_output_key in code_output_keys:
            try:
                code_output_payload = json.loads(
                    event.workflow_record.outputs[code_output_key]
                )
                # We transparently support CodeOutput[] or CodeOutput for the declared 'code' data type
                if isinstance(code_output_payload, list):
                    code_outputs.extend(
                        (CodeOutput(**payload) for payload in code_output_payload)
                    )
                else:
                    code_output = CodeOutput(**code_output_payload)
                    code_outputs.append(code_output)
            except Exception as e:
                logger.error(
                    "(roster-gha) Failed to parse code output (%s): %s",
                    code_output_key,
                    e,
                )
                continue

        code_report_payload = WorkflowCodeReportPayload(
            workflow_name=event.workflow.spec.name,
            workflow_record=event.workflow_record.id,
            code_outputs=code_outputs,
        )
        workspace_message = WorkspaceMessage(
            workspace=workspace.name,
            kind="workflow_code_report",
            data=code_report_payload.dict(),
        )

        await self.workspace_manager.handle_workspace_message(workspace_message)
