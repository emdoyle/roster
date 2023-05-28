import logging

from fastapi import APIRouter, HTTPException
from roster_api import constants, errors
from roster_api.models.team_layout import TeamLayoutSpec
from roster_api.services.team_layout import TeamLayoutService

router = APIRouter()

logger = logging.getLogger(constants.LOGGER_NAME)


@router.post("/team-layouts", tags=["TeamLayoutResource"])
def create_team_layout(team_layout: TeamLayoutSpec):
    try:
        return TeamLayoutService().create_team_layout(team_layout)
    except errors.TeamLayoutAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.get("/team-layouts", tags=["TeamLayoutResource"])
def list_team_layouts():
    return TeamLayoutService().list_team_layouts()


@router.get("/team-layouts/{name}", tags=["TeamLayoutResource"])
def get_team_layout(name: str):
    try:
        return TeamLayoutService().get_team_layout(name)
    except errors.TeamLayoutNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.patch("/team-layouts/{name}", tags=["TeamLayoutResource"])
def update_team_layout(team_layout: TeamLayoutSpec):
    try:
        return TeamLayoutService().update_team_layout(team_layout)
    except errors.TeamLayoutNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete("/team-layouts/{name}", tags=["TeamLayoutResource"])
def delete_team_layout(name: str):
    deleted = TeamLayoutService().delete_team_layout(name)
    if not deleted:
        raise HTTPException(status_code=404, detail="TeamLayout not found")
    return deleted
