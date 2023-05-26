import logging

from fastapi import APIRouter, HTTPException
from roster_api import constants, errors
from roster_api.models.role import RoleSpec
from roster_api.services.role import RoleService

router = APIRouter()

logger = logging.getLogger(constants.LOGGER_NAME)


@router.post("/roles", tags=["RoleSpec"])
def create_role(role: RoleSpec):
    try:
        return RoleService().create_role(role)
    except errors.RoleAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.get("/roles", tags=["RoleSpec"])
def list_roles():
    return RoleService().list_roles()


@router.get("/roles/{name}", tags=["RoleSpec"])
def get_role(name: str):
    try:
        return RoleService().get_role(name)
    except errors.RoleNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.patch("/roles/{name}", tags=["RoleSpec"])
def update_role(role: RoleSpec):
    try:
        return RoleService().update_role(role)
    except errors.RoleNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete("/roles/{name}", tags=["RoleSpec"])
def delete_role(name: str):
    deleted = RoleService().delete_role(name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Role not found")
    return deleted
