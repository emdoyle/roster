import logging

from fastapi import APIRouter, HTTPException
from roster_api import constants, errors
from roster_api.models.workflow import WorkflowSpec
from roster_api.services.workflow import WorkflowRecordService, WorkflowService

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


@router.get("/workflow-records", tags=["WorkflowRecord"])
def list_workflow_records(workflow_name: str = ""):
    return WorkflowRecordService().list_workflow_records(workflow_name=workflow_name)


@router.get("/workflow-records/{name}/{id}", tags=["WorkflowRecord"])
def get_workflow_record(name: str, id: str):
    try:
        return WorkflowRecordService().get_workflow_record(
            workflow_name=name, record_id=id
        )
    except errors.WorkflowRecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete("/workflow-records/{name}/{id}", tags=["WorkflowRecord"])
def delete_workflow_record(name: str, id: str):
    deleted = WorkflowRecordService().delete_workflow_record(
        workflow_name=name, record_id=id
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return deleted
