import logging

from fastapi import APIRouter, HTTPException
from roster_api import constants, errors
from roster_api.models.task import TaskSpec
from roster_api.services.task import TaskService

router = APIRouter()

logger = logging.getLogger(constants.LOGGER_NAME)


@router.post("/tasks", tags=["TaskResource"])
def create_task(task: TaskSpec):
    try:
        return TaskService().create_task(task)
    except errors.TaskAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.get("/tasks", tags=["TaskResource"])
def list_tasks():
    return TaskService().list_tasks()


@router.get("/tasks/{name}", tags=["TaskResource"])
def get_task(name: str):
    try:
        return TaskService().get_task(name)
    except errors.TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.patch("/tasks/{name}", tags=["TaskResource"])
def update_task(task: TaskSpec):
    try:
        return TaskService().update_task(task)
    except errors.TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete("/tasks/{name}", tags=["TaskResource"])
def delete_task(name: str):
    deleted = TaskService().delete_task(name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return deleted
