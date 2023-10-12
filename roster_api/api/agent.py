import logging
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from .auth import get_current_user
from fastapi import APIRouter
from roster_api import constants, errors
from roster_api.models.agent import AgentSpec
from roster_api.services.agent import AgentService

router = APIRouter()

logger = logging.getLogger(constants.LOGGER_NAME)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/agents", tags=["AgentResource"])
def create_agent(agent: AgentSpec, current_user: str = Depends(get_current_user)):
    try:
        return AgentService().create_agent(agent)
    except errors.AgentAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.message)

@router.get("/agents", tags=["AgentResource"])
def list_agents(current_user: str = Depends(get_current_user)):
    return AgentService().list_agents()

@router.get("/agents/{name}", tags=["AgentResource"])
def get_agent(name: str, current_user: str = Depends(get_current_user)):
    try:
        return AgentService().get_agent(name)
    except errors.AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)

@router.patch("/agents/{name}", tags=["AgentResource"])
def update_agent(name: str, agent: AgentSpec, current_user: str = Depends(get_current_user)):
    try:
        return AgentService().update_agent(name, agent)
    except errors.AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)

@router.delete("/agents/{name}", tags=["AgentResource"])
def delete_agent(name: str, current_user: str = Depends(get_current_user)):
    deleted = AgentService().delete_agent(name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
    return deleted
