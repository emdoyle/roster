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


class TaskError(RosterAPIError):
    """Exception raised for task-related errors."""

    def __init__(
        self,
        message="An unexpected error occurred for the Task.",
        details=None,
        task=None,
    ):
        super().__init__(message, details)
        self.task = task


class TaskAlreadyExistsError(TaskError):
    """Exception raised when a Task already exists."""

    def __init__(
        self,
        message="An Task with the specified name already exists.",
        details=None,
        task=None,
    ):
        super().__init__(message, details)
        self.task = task


class TaskNotFoundError(TaskError):
    """Exception raised when a Task is not found."""

    def __init__(
        self, message="The specified Task was not found.", details=None, task=None
    ):
        super().__init__(message, details)
        self.task = task


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


class RoleError(RosterAPIError):
    """Exception raised for role-related errors."""

    def __init__(
        self,
        message="An unexpected error occurred for the Role.",
        details=None,
        role=None,
    ):
        super().__init__(message, details)
        self.role = role


class RoleAlreadyExistsError(RoleError):
    """Exception raised when a Role already exists."""

    def __init__(
        self,
        message="A Role with the specified name already exists.",
        details=None,
        role=None,
    ):
        super().__init__(message, details)
        self.role = role


class RoleNotFoundError(RoleError):
    """Exception raised when a Role is not found."""

    def __init__(
        self, message="The specified Role was not found.", details=None, role=None
    ):
        super().__init__(message, details)
        self.role = role


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


class TeamLayoutError(RosterAPIError):
    """Exception raised for team-related errors."""

    def __init__(
        self,
        message="An unexpected error occurred for the TeamLayout.",
        details=None,
        team_layout=None,
    ):
        super().__init__(message, details)
        self.team_layout = team_layout


class TeamLayoutAlreadyExistsError(TeamLayoutError):
    """Exception raised when a TeamLayout already exists."""

    def __init__(
        self,
        message="A TeamLayout with the specified name already exists.",
        details=None,
        team_layout=None,
    ):
        super().__init__(message, details)
        self.team_layout = team_layout


class TeamLayoutNotFoundError(TeamLayoutError):
    """Exception raised when a TeamLayout is not found."""

    def __init__(
        self,
        message="The specified TeamLayout was not found.",
        details=None,
        team_layout=None,
    ):
        super().__init__(message, details)
        self.team_layout = team_layout
