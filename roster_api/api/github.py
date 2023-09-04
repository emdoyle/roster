from fastapi import APIRouter, HTTPException, Request
from roster_api.github.service import GithubService

router = APIRouter()


@router.post("/")
async def handle_webhook(request: Request):
    webhook_payload = await request.json()

    try:
        installation_id = int(webhook_payload["installation"]["id"])
        repository_name = webhook_payload["repository"]["full_name"]
    except (KeyError, ValueError):
        raise HTTPException(status_code=400)

    github_manager = GithubService(
        installation_id=installation_id, repository_name=repository_name
    )

    if "issue" in webhook_payload and webhook_payload["action"] in [
        "opened",
        "reopened",
    ]:
        await github_manager.handle_issue_created(payload=webhook_payload)
    elif "issue" in webhook_payload and "comment" in webhook_payload:
        await github_manager.handle_issue_comment(payload=webhook_payload)