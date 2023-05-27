import logging

from fastapi import APIRouter, HTTPException
from roster_api import constants, errors
from roster_api.models.agent import AgentSpec
from roster_api.services.agent import AgentService

router = APIRouter()

logger = logging.getLogger(constants.LOGGER_NAME)


@router.post("/agents", tags=["AgentSpec"])
def create_agent(agent: AgentSpec):
    try:
        return AgentService().create_agent(agent)
    except errors.AgentAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.get("/agents", tags=["AgentSpec"])
def list_agents():
    return AgentService().list_agents()


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
