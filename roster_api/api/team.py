
import logging

from fastapi import APIRouter, HTTPException
from roster_api import constants, errors
from roster_api.models.team import TeamSpec
from roster_api.services.team import TeamService

router = APIRouter()

logger = logging.getLogger(constants.LOGGER_NAME)


@router.post("/teams", tags=["TeamResource"])
def create_team(team: TeamSpec):
    try:
        return TeamService().create_team(team)
    except errors.TeamAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.get("/teams", tags=["TeamResource"])
def list_teams():
    return TeamService().list_teams()


@router.get("/teams/{name}", tags=["TeamResource"])
def get_team(name: str):
    try:
        return TeamService().get_team(name)
    except errors.TeamNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.patch("/teams", tags=["TeamResource"])
def update_team(team: TeamSpec):
    try:
        return TeamService().update_team(team)
    except errors.TeamNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete("/teams/{name}", tags=["TeamResource"])
def delete_team(name: str):
    deleted = TeamService().delete_team(name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Team not found")
    return deleted
