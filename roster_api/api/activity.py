import logging
import asyncpg
from fastapi import APIRouter, FastAPI, Depends, HTTPException
from roster_api import constants
from roster_api.db.postgres import get_postgres_connection
from roster_api.models.activity import ActivityEvent, ExecutionType
from roster_api.services.activity import ActivityService

router = APIRouter()

logger = logging.getLogger(constants.LOGGER_NAME)


async def get_activity_service(
    conn: asyncpg.Connection = Depends(get_postgres_connection),
) -> "ActivityService":
    return ActivityService(conn=conn)

@router.post("/activities", tags=["ActivityEvent"])
async def create_activity(
    activity: ActivityEvent, service: ActivityService = Depends(get_activity_service)
):
    if not activity:
        raise HTTPException(status_code=400, detail="ActivityEvent cannot be None")
    await service.store_activity(activity)
    return True

@router.get("/activities", tags=["ActivityEvent"])
async def read_activities(
    execution_id: str,
    execution_type: ExecutionType,
    service: ActivityService = Depends(get_activity_service),
):
    if not execution_id or not execution_type:
        raise HTTPException(status_code=400, detail="Execution ID and Type cannot be None")
    activities = await service.fetch_activities(execution_id, execution_type)
    return activities
