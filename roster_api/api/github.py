from fastapi import APIRouter, Depends, HTTPException, Request
from roster_api import errors
from roster_api.github.app import RosterGithubApp
from roster_api.singletons import get_roster_github_app

router = APIRouter()


@router.post("")
async def handle_webhook(
    request: Request, github_app: RosterGithubApp = Depends(get_roster_github_app)
):
    webhook_payload = await request.json()

    try:
        await github_app.handle_webhook_payload(webhook_payload)
    except errors.GithubWebhookError:
        raise HTTPException(status_code=400)
