import logging.handlers
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from roster_api.watchers.all import setup_watchers, teardown_watchers

from . import constants, settings
from .api.state.agent import router as agent_router

logger = logging.getLogger(constants.LOGGER_NAME)
logger.setLevel(settings.SERVER_LOG_LEVEL)

logs_enabled = False


def setup_logging():
    global logs_enabled
    if logs_enabled:
        # logging already setup,
        # don't add new handlers
        return
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_log_format = "%(levelname)s:\t [log] %(message)s"
    console_format = logging.Formatter(console_log_format)
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    file_handler = logging.handlers.RotatingFileHandler(
        settings.SERVER_LOG, maxBytes=1000000
    )
    file_handler.setLevel(logging.DEBUG)
    file_log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_format = logging.Formatter(file_log_format)
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    logs_enabled = True


async def setup():
    setup_logging()
    setup_watchers()


async def teardown():
    teardown_watchers()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await setup()
        yield
    finally:
        await teardown()


def get_app():
    app = FastAPI(title="Roster API", version="0.1.0", lifespan=lifespan)
    app.include_router(agent_router, prefix=f"/api/{constants.API_VERSION}")
    return app


def main():
    app = get_app()
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)


if __name__ == "__main__":
    main()
