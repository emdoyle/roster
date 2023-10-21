import json
import logging
from typing import List

import asyncpg
from code_index import constants
from code_index.models.activity import ActivityEvent, ExecutionType

logger = logging.getLogger(constants.LOGGER_NAME)


class ActivityService:
    def __init__(self, conn: asyncpg.Connection):
        self.conn: asyncpg.Connection = conn

    async def store_activity(self, activity: ActivityEvent):
        activity_dict = activity.dict()
        activity_dict["execution_type"] = activity_dict["execution_type"].value
        activity_dict["type"] = activity_dict["type"].value
        activity_dict["agent_context"] = json.dumps(activity_dict["agent_context"])
        await self.conn.execute(
            """
            INSERT INTO activity_events (execution_id, execution_type, type, content, agent_context)
            VALUES ($1, $2, $3, $4, $5)
            """,
            activity_dict["execution_id"],
            activity_dict["execution_type"],
            activity_dict["type"],
            activity_dict["content"],
            activity_dict["agent_context"],
        )

    async def fetch_activities(
        self, execution_id: str, execution_type: ExecutionType
    ) -> List[ActivityEvent]:
        records = await self.conn.fetch(
            """
            SELECT * FROM activity_events
            WHERE execution_id = $1 AND execution_type = $2
            """,
            execution_id,
            execution_type.value,
        )
        return [
            ActivityEvent(
                **{**record, "agent_context": json.loads(record["agent_context"])}
            )
            for record in records
        ]
