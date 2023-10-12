import logging

from fastapi import APIRouter, HTTPException
from roster_api import constants, errors
from roster_api.models.identity import IdentitySpec
from roster_api.services.identity import IdentityService

router = APIRouter()

logger = logging.getLogger(constants.LOGGER_NAME)


@router.post("/identities", tags=["IdentityResource"])
def create_identity(identity: IdentitySpec):
    try:
        return IdentityService().create_identity(identity)
    except errors.IdentityAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.get("/identities", tags=["IdentityResource"])
def list_identities():
    return IdentityService().list_identities()


@router.get("/identities/{name}", tags=["IdentityResource"])
def get_identity(name: str):
    try:
        return IdentityService().get_identity(name)
    except errors.IdentityNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)

@router.patch("/identities", tags=["IdentityResource"])
def update_identity(identity: IdentitySpec):
    try:
        return IdentityService().update_identity(identity)
    except errors.IdentityNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete("/identities/{name}", tags=["IdentityResource"])
def delete_identity(name: str):
    deleted = IdentityService().delete_identity(name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Identity not found")
    return deleted
