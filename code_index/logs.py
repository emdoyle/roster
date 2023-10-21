import logging

from code_index import constants, settings

logger = logging.getLogger(constants.LOGGER_NAME)
logger.setLevel(settings.SERVER_LOG_LEVEL)
APP_LOGGER = logger


def app_logger():
    return APP_LOGGER
