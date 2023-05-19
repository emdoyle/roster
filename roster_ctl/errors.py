class CLIError(Exception):
    """Base exception class for cli-related errors."""

    def __init__(self, message="An unexpected error occurred.", details=None):
        super().__init__(message, details)


class AddAgentError(CLIError):
    """Exception raised when an error occurs during add_agent."""

    def __init__(
        self, message="An error occurred when attempting to add_agent.", details=None
    ):
        super().__init__(message, details)
