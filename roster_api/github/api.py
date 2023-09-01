from typing import Optional

from fastapi import APIRouter, Request
from roster_api import settings

from github import Auth

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
    print(request, await request.json())
