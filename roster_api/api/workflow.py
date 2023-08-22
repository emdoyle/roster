import logging

from fastapi import APIRouter, HTTPException
from roster_api import constants, errors
from roster_api.models.workflow import WorkflowSpec
from roster_api.services.workflow import WorkflowService

router = APIRouter()

logger = logging.getLogger(constants.LOGGER_NAME)


@router.post("/workflows", tags=["WorkflowResource"])
def create_workflow(workflow: WorkflowSpec):
    try:
        return WorkflowService().create_workflow(workflow)
    except errors.WorkflowAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.get("/workflows", tags=["WorkflowResource"])
def list_workflows():
    return WorkflowService().list_workflows()


@router.get("/workflows/{name}", tags=["WorkflowResource"])
def get_workflow(name: str):
    try:
        return WorkflowService().get_workflow(name)
    except errors.WorkflowNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.patch("/workflows/{name}", tags=["WorkflowResource"])
def update_workflow(workflow: WorkflowSpec):
    try:
        return WorkflowService().update_workflow(workflow)
    except errors.WorkflowNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete("/workflows/{name}", tags=["WorkflowResource"])
def delete_workflow(name: str):
    deleted = WorkflowService().delete_workflow(name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return deleted
