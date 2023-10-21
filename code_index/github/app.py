import logging

from code_index import constants

logger = logging.getLogger(constants.LOGGER_NAME)


class GithubApp:
    def __init__(self):
        pass

    async def handle_webhook_payload(self, payload: dict):
        logger.debug("(github-app) Received GitHub payload: %s", payload)
