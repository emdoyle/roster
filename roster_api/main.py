from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from roster_api.watchers.all import setup_watchers, teardown_watchers

from . import constants, settings
from .api.state.agent import router as agent_router


async def setup():
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
