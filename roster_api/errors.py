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
