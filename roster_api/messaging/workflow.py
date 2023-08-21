import json
import logging

from roster_api import constants
from roster_api.messaging.rabbitmq import RabbitMQClient, get_rabbitmq

logger = logging.getLogger(constants.LOGGER_NAME)


class WorkflowRouter:
    # TODO: proper namespace support
    QUEUE_NAME = "default:actor:roster-admin:workflow-router"

    def __init__(self, rmq_client: RabbitMQClient = None):
        self.rmq = rmq_client or get_rabbitmq()

    async def setup(self) -> None:
        await self.rmq.register_callback(self.QUEUE_NAME, self.route)

    async def teardown(self) -> None:
        await self.rmq.deregister_callback(self.QUEUE_NAME, self.route)

    async def route(self, message: str) -> None:
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            logger.debug(
                "(workflow-router) Failed to decode workflow message: %s", message
            )
            return
        # TODO: actual routing logic
        logger.info("(workflow-router) Received workflow message: %s", payload)
