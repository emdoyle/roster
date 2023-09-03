from typing import Optional

from roster_api import settings
from roster_api.workspace.git import GitWorkspace

from github import Auth, Github

with open(settings.GITHUB_APP_PRIVATE_KEY, "r") as _f:
    private_key = _f.read()


def _github_auth(
    installation_id: int, token_permissions: Optional[dict[str, str]] = None
) -> Auth.AppInstallationAuth:
    # Authenticates as a Github App Installation
    #   Should be able to take actions like opening Pull Requests, responding to comments etc.
    return Auth.AppAuth(
        app_id=settings.GITHUB_APP_ID, private_key=private_key
    ).get_installation_auth(
        installation_id=installation_id, token_permissions=token_permissions
    )


class GithubWebhookService:
    def __init__(self, installation_id: int, repository_name: str):
        self.installation_id = installation_id
        self.repository_name = repository_name
        self.gh_auth = _github_auth(installation_id=installation_id)
        self.gh = Github(auth=self.gh_auth)
        simple_repo_name = repository_name.split("/")[-1]
        self.workspace = GitWorkspace(
            root_dir=f"{settings.WORKSPACE_DIR}/{installation_id}/{simple_repo_name}"
        )

    async def handle_issue_created(self, payload: dict):
        """Use GitWorkspace to clone the repo to a local workspace directory"""
        try:
            issue_number = payload["issue"]["number"]
        except KeyError:
            raise ValueError(f"Malformed issue created payload: {payload}")

        repo = self.gh.get_repo(self.repository_name)
        issue = repo.get_issue(issue_number)
        issue.create_comment("Thanks for opening this issue! Roster is working on it.")

    async def handle_issue_comment(self, payload: dict):
        try:
            issue_number = payload["issue"]["number"]
            comment_id = payload["comment"]["id"]
        except KeyError:
            raise ValueError(f"Malformed issue comment payload: {payload}")

        repo = self.gh.get_repo(self.repository_name)
        issue = repo.get_issue(issue_number)
        comment = issue.get_comment(comment_id)

        if comment.user.login == "roster-ai[bot]":
            return
        comment.create_reaction("heart")
