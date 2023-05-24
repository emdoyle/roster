import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from roster_api import errors
from roster_api.models.agent import AgentSpec
from roster_api.services.agent import AgentService
from roster_api.watchers.agent import get_agent_resource_watcher

router = APIRouter()


@router.post("/agents", tags=["AgentSpec"])
def create_agent(agent: AgentSpec):
    try:
        return AgentService().create_agent(agent)
    except errors.AgentAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.get("/agents/{name}", tags=["AgentSpec"])
def get_agent(name: str):
    try:
        return AgentService().get_agent(name)
    except errors.AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.patch("/agents/{name}", tags=["AgentSpec"])
def update_agent(agent: AgentSpec):
    try:
        return AgentService().update_agent(agent)
    except errors.AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete("/agents/{name}", tags=["AgentSpec"])
def delete_agent(name: str):
    deleted = AgentService().delete_agent(name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
    return deleted


@router.get("/agent-events")
async def events():

    event_queue = asyncio.Queue()

    def listener(event):
        event_queue.put_nowait(f"data: {event}\n\n")

    async def event_stream():
        while True:
            try:
                yield await event_queue.get()
            except Exception:
                get_agent_resource_watcher().remove_listener(listener)

    get_agent_resource_watcher().add_listener(listener)

    response = StreamingResponse(event_stream(), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["Transfer-Encoding"] = "chunked"

    return response
