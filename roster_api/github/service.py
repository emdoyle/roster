from typing import Optional

from roster_api import settings

from github import Auth, Github, GithubException

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


class GithubService:
    def __init__(
        self,
        installation_id: int,
        repository_name: str,
    ):
        self.installation_id = installation_id
        self.repository_name = repository_name
        self.gh_auth = _github_auth(installation_id=installation_id)
        self.gh = Github(auth=self.gh_auth)

    def get_installation_token(self) -> str:
        return self.gh_auth.token

    def get_repo_url(self) -> str:
        repo = self.gh.get_repo(self.repository_name)
        return repo.clone_url

    def create_pull_request(
        self, title: str, body: str, head: str, base: str = "main"
    ) -> str:
        repo = self.gh.get_repo(self.repository_name)
        try:
            pr = repo.create_pull(title=title, body=body, head=head, base=base)
            return pr.html_url
        except GithubException as e:
            raise ValueError(f"Failed to create a pull request: {e}") from e

    async def handle_issue_created(self, payload: dict):
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

        if comment.user.login == f"{settings.GITHUB_APP_NAME}[bot]":
            return
        comment.create_reaction("heart")
