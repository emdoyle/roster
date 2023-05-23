import uvicorn
from fastapi import FastAPI

from . import settings
from .api.state.agent import router as agent_router


def get_app():
    app = FastAPI(title="Roster API", version="0.1.0")
    app.include_router(agent_router)
    return app


def main():
    app = get_app()
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)


if __name__ == "__main__":
    main()
