import asyncio
import logging.handlers
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from code_index.db.postgres import setup_postgres, teardown_postgres
from code_index.messaging.rabbitmq import setup_rabbitmq, teardown_rabbitmq
from code_index.singletons import get_github_app

from . import constants, settings
from .api.github import router as github_router

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


github_app = get_github_app()


async def setup():
    setup_logging()
    await asyncio.gather(setup_postgres(), setup_rabbitmq())


async def teardown():
    await asyncio.gather(teardown_postgres(), teardown_rabbitmq())


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await setup()
        yield
    finally:
        await teardown()


def get_app():
    app = FastAPI(title="Code Indexer API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(github_router, prefix="/github")
    return app


def main():
    app = get_app()
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)


if __name__ == "__main__":
    main()
