from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from code_index.github.app import GithubApp

GITHUB_APP: Optional["GithubApp"] = None


def get_github_app() -> "GithubApp":
    global GITHUB_APP
    if GITHUB_APP is not None:
        return GITHUB_APP

    from code_index.github.app import GithubApp

    GITHUB_APP = GithubApp()
    return GITHUB_APP
