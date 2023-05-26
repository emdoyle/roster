import logging

from fastapi import APIRouter, HTTPException, Request
from roster_api import constants, errors
from roster_api.events.status import StatusEvent
from roster_api.services.agent import AgentService

router = APIRouter()

logger = logging.getLogger(constants.LOGGER_NAME)


@router.post("/status-update")
async def handle_status_update(request: Request, status_update: StatusEvent):
    status_update.host_ip = request.client.host
    if status_update.resource_type == "AGENT":
        try:
            AgentService().handle_agent_status_update(status_update=status_update)
            return {"message": "OK"}
        except errors.AgentNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.message)
        except errors.InvalidEventError as e:
            raise HTTPException(status_code=400, detail=e.message)
    else:
        logger.warning(
            f"Received status update for unknown resource type: {status_update.resource_type}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Received status update for unknown resource type: {status_update.resource_type}",
        )
