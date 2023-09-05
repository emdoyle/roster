import asyncio
import logging.handlers
from contextlib import asynccontextmanager

import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from roster_api.db.postgres import setup_postgres, teardown_postgres
from roster_api.messaging.rabbitmq import setup_rabbitmq, teardown_rabbitmq
from roster_api.singletons import (get_roster_github_app, get_workflow_router,
                                   get_workspace_manager)
from roster_api.watchers.all import setup_watchers, teardown_watchers

from . import constants, settings
from .api.activity import router as activity_router
from .api.agent import router as agent_router
from .api.commands import router as commands_router
from .api.identity import router as identity_router
from .api.team import router as team_router
from .api.updates import router as updates_router
from .api.workflow import router as workflow_router

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


workflow_message_router = get_workflow_router()
workspace_manager = get_workspace_manager()
roster_github_app = get_roster_github_app()


async def setup():
    setup_logging()
    await asyncio.gather(setup_postgres(), setup_rabbitmq())
    # NOTE: etcd uses a separate Thread due to blocking I/O
    #   currently does not kill the main thread on connection error (but probably should)
    setup_watchers()
    # Other high-level controllers, actors setup here
    # TODO: consider moving within roster_orchestration?
    await asyncio.gather(workflow_message_router.setup(), workspace_manager.setup())
    await roster_github_app.setup()


async def teardown():
    # Other high-level controllers, actors teardown here
    await roster_github_app.teardown()
    await asyncio.gather(
        workflow_message_router.teardown(), workspace_manager.teardown()
    )
    teardown_watchers()
    await asyncio.gather(teardown_postgres(), teardown_rabbitmq())


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await setup()
        yield
    finally:
        await teardown()


def get_app():
    app = FastAPI(title="Roster API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )

    api_router = APIRouter()

    api_router.include_router(agent_router)
    api_router.include_router(activity_router)
    api_router.include_router(identity_router)
    api_router.include_router(team_router)
    api_router.include_router(updates_router)
    api_router.include_router(workflow_router)
    api_router.include_router(commands_router, prefix="/commands")

    app.include_router(api_router, prefix=f"/{constants.API_VERSION}")
    return app


def main():
    app = get_app()
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)


if __name__ == "__main__":
    main()
