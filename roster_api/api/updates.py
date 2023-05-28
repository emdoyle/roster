import asyncio
import logging
from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from roster_api import constants, errors
from roster_api.events.spec import ResourceEvent
from roster_api.events.status import StatusEvent
from roster_api.services.agent import AgentService
from roster_api.watchers.resource import get_resource_watcher

router = APIRouter()

logger = logging.getLogger(constants.LOGGER_NAME)


@router.get("/resource-events", tags=["Event"])
async def events(
    request: Request,
    resource_types: Annotated[Optional[list[str]], Query()] = None,
    spec_changes: bool = True,
    status_changes: bool = True,
):
    if not spec_changes and not status_changes:
        raise HTTPException(
            status_code=400, detail="Must specify at least one type of change"
        )

    event_queue = asyncio.Queue()

    def listener(event: ResourceEvent):
        if resource_types is not None and event.resource_type not in resource_types:
            # This listener doesn't care about this event's resource type
            return
        if (
            event.event_type == "DELETE"
            or (spec_changes and event.spec_changed)
            or (status_changes and event.status_changed)
        ):
            # This listener cares about this event's changes
            event_queue.put_nowait(event.serialize() + b"\n\n")

    async def event_stream():
        try:
            while True:
                if await request.is_disconnected():
                    logger.debug(f"Client disconnected ({request.client.host})")
                    break

                result = await event_queue.get()
                logger.debug(f"SSE Send ({request.client.host})")
                yield result
        except asyncio.CancelledError:
            logger.debug(f"Stopping SSE stream for {request.client.host}")
            get_resource_watcher().remove_listener(listener)

    get_resource_watcher().add_listener(listener)

    response = StreamingResponse(event_stream(), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["Transfer-Encoding"] = "chunked"

    logger.debug(f"Started SSE stream for {request.client.host}")
    return response


@router.post("/status-update", tags=["Event"])
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
