import asyncio
import json
import logging
from typing import Optional
import pydantic
from roster_api import constants
from roster_api.github.codebase_tools.tree import build_codebase_tree
from roster_api.github.service import GithubService
from roster_api.messaging.inbox import AgentInbox
from roster_api.messaging.rabbitmq import RabbitMQClient, get_rabbitmq
from roster_api.models.tool import ToolMessage
from roster_api.models.workspace import WorkflowCodeReportPayload, WorkspaceMessage
from roster_api.services.workflow import WorkflowRecordService
from roster_api.services.workspace import WorkspaceService

from .git import GitWorkspace

logger = logging.getLogger(constants.LOGGER_NAME)


class WorkspaceManager:
    def __init__(self, rmq_client: Optional[RabbitMQClient] = None):
        self.rmq = rmq_client or get_rabbitmq()
        self._fs_lock = asyncio.Lock()
    async def setup(self):
        await self.rmq.register_callback(
            constants.WORKSPACE_QUEUE, self._handle_incoming_message
        )

    async def teardown(self):
        await self.rmq.deregister_callback(
            constants.WORKSPACE_QUEUE, self._handle_incoming_message
        )
    async def build_codebase_tree(self, github_service: GithubService) -> str:
        async with self._fs_lock:
            git_workspace = GitWorkspace.setup(
                installation_id=github_service.installation_id,
                repository_name=github_service.repository_name,
                repo_url=github_service.get_repo_url(),
                token=github_service.get_installation_token(),
            )
            git_workspace.force_to_latest()
            return build_codebase_tree(git_workspace.root_dir)
    async def get_base_hash(
        self, github_service: GithubService, branch: str = "main"
    ) -> str:
        async with self._fs_lock:
            git_workspace = GitWorkspace.setup(
                installation_id=github_service.installation_id,
                repository_name=github_service.repository_name,
                repo_url=github_service.get_repo_url(),
                token=github_service.get_installation_token(),
            )
            git_workspace.force_to_latest()
            if branch != "main":
                # TODO: should have a way to pull local branch up to origin if it exists
                #   (internal to GitWorkspace)
                git_workspace.checkout_branch(branch=branch)
            return git_workspace.get_current_head_sha()
    async def _handle_incoming_message(self, message: str):
        try:
            message_data = json.loads(message)
        except json.JSONDecodeError as e:
            logger.error("(workspace-mgr) Failed to decode message: %s", e)
            return

        try:
            message_kind = message_data["kind"]
        except KeyError as e:
            logger.error("(workspace-mgr) Missing key in message: %s", e)
            return

        try:
            if message_kind == "workflow_code_report":
                await self.handle_workspace_message(
                    message=WorkspaceMessage(**message_data)
                )
            elif message_kind == "tool_invocation":
                await self.handle_tool_message(message=ToolMessage(**message_data))
            else:
                logger.debug("(workspace-mgr) Unknown message kind: %s", message_kind)
        except pydantic.ValidationError as e:
            logger.error(
                "(workspace-mgr) Failed to validate message: %s, %s", message_data, e
            )
    async def handle_workspace_message(self, message: WorkspaceMessage):
        try:
            message_payload = WorkflowCodeReportPayload(**message.data)
        except pydantic.ValidationError as e:
            logger.error(
                "(workspace-mgr) Failed to validate workflow code report payload: %s", e
            )
            return

        workspace = WorkspaceService().get_workspace(message.workspace)
        if workspace.kind != "github":
            logger.debug("(workspace-mgr) Unknown workspace kind: %s", workspace.kind)
            return

        github_info = workspace.github_info
        if not github_info:
            logger.debug("(workspace-mgr) No github info provided by workspace message")
            return

        github_service = GithubService(
            installation_id=github_info.installation_id,
            repository_name=github_info.repository_name,
        )

        async with self._fs_lock:
            git_workspace = GitWorkspace.setup(
                installation_id=github_service.installation_id,
                repository_name=github_service.repository_name,
                repo_url=github_service.get_repo_url(),
                token=github_service.get_installation_token(),
            )
            git_workspace.force_to_latest()
            # TODO: should have a way to pull local branch up to origin if it exists
            #   (internal to GitWorkspace)
            git_workspace.checkout_branch(github_info.branch_name)

            for code_output in message_payload.code_outputs:
                with git_workspace.open(code_output.filepath, "w") as f:
                    # TODO: support other code_output kinds
                    f.write(code_output.content)

            git_workspace.commit(
                f"Committing changes from workflow {message_payload.workflow_name} ({message_payload.workflow_record})"
            )
            git_workspace.push()

        # TODO: send better metadata for PRs, commit messages through message payload
        pr_url = github_service.create_pull_request(
            title=f"[roster-ai] {message_payload.workflow_name} ({message_payload.workflow_record})",
            body="This Pull Request was generated by Roster! :star:",
            head=github_info.branch_name,
        )
        logger.info("Created PR for %s: %s", github_info.repository_name, pr_url)
    async def handle_tool_message(self, message: ToolMessage):
        if message.sender is None:
            logger.debug(
                "(workspace-mgr) ToolMessage missing return address: %s", message
            )
            return

        agent_inbox = AgentInbox(
            name=message.sender.name, namespace=message.sender.namespace
        )
        try:
            if message.tool == "workspace-file-reader":
                result = await self._tool_workspace_file_reader(message=message)
            else:
                logger.debug(
                    "(workspace-mgr) Unknown tool for WorkspaceManager: %s",
                    message.tool,
                )
                return
        except Exception as e:
            await agent_inbox.send_tool_response(
                invocation_id=message.id,
                tool=message.tool,
                error=f"Failed to run tool: {e}",
            )
        else:
            await agent_inbox.send_tool_response(
                invocation_id=message.id, tool=message.tool, data=result
            )
    async def _tool_workspace_file_reader(self, message: ToolMessage) -> dict:
        # NOTE: input format is data={inputs: {record_id: ..., workflow: ..., filepaths: ...}}
        #   and output format is data={files: [{filename: ..., text: ..., metadata: ...}, ...]}
        try:
            inputs = message.data["inputs"]
            record_id = inputs["record_id"]
            workflow = inputs["workflow"]
            filepaths = inputs["filepaths"]
        except KeyError as e:
            logger.debug(
                "(workspace-mgr) Missing key in workspace file reader message: %s", e
            )
            raise KeyError("Missing key in workspace file reader message")

        workflow_record = WorkflowRecordService().get_workflow_record(
            record_id=record_id, workflow_name=workflow
        )
        if not workflow_record.workspace:
            logger.debug(
                "(workspace-mgr) Workflow record %s has no workspace", workflow_record
            )
            raise ValueError("No workspace found for workflow record")
        workspace = WorkspaceService().get_workspace(workflow_record.workspace)

        if workspace.kind != "github":
            logger.debug("(workspace-mgr) Unknown workspace kind: %s", workspace.kind)
            raise ValueError(f"Workspace has unknown kind: {workspace.kind}")

        github_info = workspace.github_info
        if not github_info:
            logger.debug("(workspace-mgr) No github info provided by workspace message")
            raise ValueError("Workspace has no github info")

        github_service = GithubService(
            installation_id=github_info.installation_id,
            repository_name=github_info.repository_name,
        )
        output_files = []
        async with self._fs_lock:
            git_workspace = GitWorkspace.setup(
                installation_id=github_service.installation_id,
                repository_name=github_service.repository_name,
                repo_url=github_service.get_repo_url(),
                token=github_service.get_installation_token(),
            )
            git_workspace.checkout_sha(github_info.base_hash)
            for filepath in filepaths:
                with git_workspace.open(filepath, "r") as f:
                    output_files.append({"filename": filepath, "text": f.read()})

        return {"files": output_files}
