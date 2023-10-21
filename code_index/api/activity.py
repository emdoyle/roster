import logging

import asyncpg
from fastapi import APIRouter, Depends
from code_index import constants
from code_index.db.postgres import get_postgres_connection
from code_index.models.activity import ActivityEvent, ExecutionType
from code_index.services.activity import ActivityService

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
    await service.store_activity(activity)
    return True


# This retrieves all stored activities matching the filters.
# Streaming is not implemented because listen/notify is unnecessary for an MVP.
# The client will be responsible for polling/dedupe by ID.
@router.get("/activities", tags=["ActivityEvent"])
async def read_activities(
    execution_id: str,
    execution_type: ExecutionType,
    service: ActivityService = Depends(get_activity_service),
):
    activities = await service.fetch_activities(execution_id, execution_type)
    return activities
