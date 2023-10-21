import logging

from fastapi import APIRouter, HTTPException
from code_index import constants, errors
from code_index.models.agent import AgentSpec
from code_index.services.agent import AgentService

router = APIRouter()

logger = logging.getLogger(constants.LOGGER_NAME)


@router.post("/agents", tags=["AgentResource"])
def create_agent(agent: AgentSpec):
    try:
        return AgentService().create_agent(agent)
    except errors.AgentAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.get("/agents", tags=["AgentResource"])
def list_agents():
    return AgentService().list_agents()


@router.get("/agents/{name}", tags=["AgentResource"])
def get_agent(name: str):
    try:
        return AgentService().get_agent(name)
    except errors.AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.patch("/agents/{name}", tags=["AgentResource"])
def update_agent(agent: AgentSpec):
    try:
        return AgentService().update_agent(agent)
    except errors.AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete("/agents/{name}", tags=["AgentResource"])
def delete_agent(name: str):
    deleted = AgentService().delete_agent(name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
    return deleted
