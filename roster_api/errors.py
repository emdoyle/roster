class RosterAPIError(Exception):
    """Base exception class for exceptions in this module."""

    def __init__(self, message="An unexpected error occurred.", details=None):
        super().__init__(message, details)
        self.message = message
        self.details = details


class AgentError(RosterAPIError):
    """Exception raised for agent-related errors."""

    def __init__(
        self,
        message="An unexpected error occurred for the Agent.",
        details=None,
        agent=None,
    ):
        super().__init__(message, details)
        self.agent = agent


class AgentAlreadyExistsError(AgentError):
    """Exception raised when an Agent already exists."""

    def __init__(
        self,
        message="An Agent with the specified name already exists.",
        details=None,
        agent=None,
    ):
        super().__init__(message, details)
        self.agent = agent


class AgentNotFoundError(AgentError):
    """Exception raised when an Agent is not found."""

    def __init__(
        self, message="The specified Agent was not found.", details=None, agent=None
    ):
        super().__init__(message, details)
        self.agent = agent


class AgentNotReadyError(AgentError):
    """Exception raised when an Agent is not ready."""

    def __init__(
        self, message="The specified Agent is not ready.", details=None, agent=None
    ):
        super().__init__(message, details)
        self.agent = agent


class WorkflowError(RosterAPIError):
    """Exception raised for workflow-related errors."""

    def __init__(
        self,
        message="An unexpected error occurred for the Workflow.",
        details=None,
        workflow=None,
    ):
        super().__init__(message, details)
        self.workflow = workflow


class WorkflowAlreadyExistsError(WorkflowError):
    """Exception raised when a Workflow already exists."""

    def __init__(
        self,
        message="A Workflow with the specified name already exists.",
        details=None,
        workflow=None,
    ):
        super().__init__(message, details)
        self.workflow = workflow


class WorkflowNotFoundError(WorkflowError):
    """Exception raised when a Workflow is not found."""

    def __init__(
        self,
        message="The specified Workflow was not found.",
        details=None,
        workflow=None,
    ):
        super().__init__(message, details)
        self.workflow = workflow


class WorkflowNotReadyError(WorkflowError):
    """Exception raised when a Workflow is not ready."""

    def __init__(
        self,
        message="The specified Workflow is not ready.",
        details=None,
        workflow=None,
    ):
        super().__init__(message, details)
        self.workflow = workflow


class WorkflowRecordError(RosterAPIError):
    """Exception raised for WorkflowRecord-related errors."""

    def __init__(
        self,
        message="An unexpected error occurred for the WorkflowRecord.",
        details=None,
        workflow=None,
        record=None,
    ):
        super().__init__(message, details)
        self.workflow = workflow
        self.record = record


class WorkflowRecordAlreadyExistsError(WorkflowRecordError):
    """Exception raised when a WorkflowRecord already exists."""

    def __init__(
        self,
        message="A WorkflowRecord with the specified name already exists.",
        details=None,
        workflow=None,
        record=None,
    ):
        super().__init__(message, details)
        self.workflow = workflow
        self.record = record


class WorkflowRecordNotFoundError(WorkflowRecordError):
    """Exception raised when a WorkflowRecord is not found."""

    def __init__(
        self,
        message="The specified WorkflowRecord was not found.",
        details=None,
        workflow=None,
        record=None,
    ):
        super().__init__(message, details)
        self.workflow = workflow
        self.record = record


class ListenerDisconnectedError(RosterAPIError):
    """Exception raised when a listener is disconnected."""

    def __init__(
        self,
        message="The listener is disconnected.",
        details=None,
        listener=None,
    ):
        super().__init__(message, details)
        self.listener = listener


class InvalidEventError(RosterAPIError):
    """Exception raised when an invalid event is received."""

    def __init__(
        self,
        message="The event is invalid.",
        details=None,
        event=None,
    ):
        super().__init__(message, details)
        self.event = event


class InvalidResourceError(RosterAPIError):
    """Exception raised when an invalid resource is received."""

    def __init__(
        self,
        message="The resource is invalid.",
        details=None,
        resource=None,
    ):
        super().__init__(message, details)
        self.resource = resource


class DeserializationError(RosterAPIError):
    """Exception raised when object data cannot be deserialized."""

    def __init__(
        self,
        message="The data is invalid.",
        details=None,
        data=None,
    ):
        super().__init__(message, details)
        self.data = data


class IdentityError(RosterAPIError):
    """Exception raised for identity-related errors."""

    def __init__(
        self,
        message="An unexpected error occurred for the Identity.",
        details=None,
        identity=None,
    ):
        super().__init__(message, details)
        self.identity = identity


class IdentityAlreadyExistsError(IdentityError):
    """Exception raised when an Identity already exists."""

    def __init__(
        self,
        message="An Identity with the specified name already exists.",
        details=None,
        identity=None,
    ):
        super().__init__(message, details)
        self.identity = identity


class IdentityNotFoundError(IdentityError):
    """Exception raised when an Identity is not found."""

    def __init__(
        self,
        message="The specified Identity was not found.",
        details=None,
        identity=None,
    ):
        super().__init__(message, details)
        self.identity = identity


class TeamError(RosterAPIError):
    """Exception raised for team-related errors."""

    def __init__(
        self,
        message="An unexpected error occurred for the Team.",
        details=None,
        team=None,
    ):
        super().__init__(message, details)
        self.team = team


class TeamAlreadyExistsError(TeamError):
    """Exception raised when a Team already exists."""

    def __init__(
        self,
        message="A Team with the specified name already exists.",
        details=None,
        team=None,
    ):
        super().__init__(message, details)
        self.team = team


class TeamNotFoundError(TeamError):
    """Exception raised when a Team is not found."""

    def __init__(
        self, message="The specified Team was not found.", details=None, team=None
    ):
        super().__init__(message, details)
        self.team = team


class TeamRoleNotFoundError(RosterAPIError):
    """Exception raised when a role is not found."""

    def __init__(
        self,
        message="The specified role was not found.",
        details=None,
        role=None,
    ):
        super().__init__(message, details)
        self.role = role


class TeamMemberNotFoundError(RosterAPIError):
    """Exception raised when a TeamMember is not found."""

    def __init__(
        self,
        message="The specified member was not found.",
        details=None,
        member=None,
    ):
        super().__init__(message, details)
        self.member = member


class SetupError(RosterAPIError):
    """Exception raised for setup-related errors."""

    def __init__(
        self,
        message="An unexpected error occurred during setup.",
        details=None,
    ):
        super().__init__(message, details)


class TeardownError(RosterAPIError):
    """Exception raised for teardown-related errors."""

    def __init__(
        self,
        message="An unexpected error occurred during teardown.",
        details=None,
    ):
        super().__init__(message, details)


class WorkspaceError(RosterAPIError):
    """Exception raised for workspace-related errors."""

    def __init__(
        self,
        message="An unexpected error occurred for the Workspace.",
        details=None,
        workspace=None,
    ):
        super().__init__(message, details)
        self.workspace = workspace


class WorkspaceAlreadyExistsError(WorkspaceError):
    """Exception raised when a Workspace already exists."""

    def __init__(
        self,
        message="A Workspace with the specified name already exists.",
        details=None,
        workspace=None,
    ):
        super().__init__(message, details)
        self.workspace = workspace


class WorkspaceNotFoundError(WorkspaceError):
    """Exception raised when a Workspace is not found."""

    def __init__(
        self,
        message="The specified Workspace was not found.",
        details=None,
        workspace=None,
    ):
        super().__init__(message, details)
        self.workspace = workspace


class GithubWebhookError(RosterAPIError):
    """Exception raised for GitHub webhook-related errors"""
