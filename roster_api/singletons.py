from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from roster_api.github.app import RosterGithubApp
    from roster_api.messaging.workflow import WorkflowRouter
    from roster_api.workspace.manager import WorkspaceManager

WORKFLOW_ROUTER: Optional["WorkflowRouter"] = None
WORKSPACE_MANAGER: Optional["WorkspaceManager"] = None
ROSTER_GITHUB_APP: Optional["RosterGithubApp"] = None


def get_workflow_router() -> "WorkflowRouter":
    global WORKFLOW_ROUTER
    if WORKFLOW_ROUTER is not None:
        return WORKFLOW_ROUTER

    from roster_api.messaging.workflow import WorkflowRouter

    WORKFLOW_ROUTER = WorkflowRouter()
    return WORKFLOW_ROUTER


def get_workspace_manager() -> "WorkspaceManager":
    global WORKSPACE_MANAGER
    if WORKSPACE_MANAGER is not None:
        return WORKSPACE_MANAGER

    from roster_api.workspace.manager import WorkspaceManager

    WORKSPACE_MANAGER = WorkspaceManager()
    return WORKSPACE_MANAGER


def get_roster_github_app() -> "RosterGithubApp":
    global ROSTER_GITHUB_APP
    if ROSTER_GITHUB_APP is not None:
        return ROSTER_GITHUB_APP

    from roster_api.github.app import RosterGithubApp

    ROSTER_GITHUB_APP = RosterGithubApp()
    return ROSTER_GITHUB_APP
