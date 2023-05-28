import logging

from fastapi import APIRouter, HTTPException
from roster_api import constants, errors
from roster_api.models.chat import ConversationMessage
from roster_api.services.agent import AgentService

router = APIRouter()

logger = logging.getLogger(constants.LOGGER_NAME)


@router.post("/commands/agent-chat/{name}", tags=["AgentResource", "Command"])
async def chat_prompt_agent(
    name: str,
    history: list[ConversationMessage],
    message: ConversationMessage,
):
    try:
        return await AgentService().chat_prompt_agent(name, history, message)
    except errors.AgentNotFoundError as e:
        logger.error(e.message)
        raise HTTPException(status_code=404, detail=e.message)
    except errors.AgentNotReadyError as e:
        logger.error(e.message)
        raise HTTPException(status_code=404, detail=e.message)
