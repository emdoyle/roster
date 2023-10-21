class CodeIndexError(Exception):
    """Base exception class for exceptions in this module."""


class SetupError(CodeIndexError):
    """Exception raised for setup-related errors."""


class TeardownError(CodeIndexError):
    """Exception raised for teardown-related errors."""


class GithubWebhookError(CodeIndexError):
    """Exception raised for GitHub webhook-related errors"""
