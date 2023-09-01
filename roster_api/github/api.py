from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from roster_api import settings

from github import Auth, Github

router = APIRouter()

with open(settings.GITHUB_APP_PRIVATE_KEY, "r") as f:
    private_key = f.read()


def _github_auth(
    installation_id: int, token_permissions: Optional[dict[str, str]] = None
) -> Auth:
    # Authenticates as a Github App Installation
    #   Should be able to take actions like opening Pull Requests, responding to comments etc.
    return Auth.AppAuth(
        app_id=settings.GITHUB_APP_ID, private_key=private_key
    ).get_installation_auth(
        installation_id=installation_id, token_permissions=token_permissions
    )


@router.post("/")
async def handle_webhook(request: Request):
    webhook_payload = await request.json()
    try:
        installation_id = int(webhook_payload["installation"]["id"])
        repository_name = webhook_payload["repository"]["full_name"]
        issue_number = webhook_payload["issue"]["number"]
        comment_id = webhook_payload["comment"]["id"]
    except (KeyError, ValueError):
        raise HTTPException(status_code=400)

    auth = _github_auth(installation_id=installation_id)
    gh = Github(auth=auth)
    repo = gh.get_repo(repository_name)
    issue = repo.get_issue(issue_number)
    comment = issue.get_comment(comment_id)
    comment.create_reaction("heart")
    return {}
