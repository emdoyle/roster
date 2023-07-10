import logging

from fastapi import APIRouter, HTTPException
from roster_api import constants, errors
from roster_api.models.chat import ChatPromptAgentArgs, ConversationMessage
from roster_api.services.agent import AgentService
from roster_api.services.team import TeamService

router = APIRouter()

logger = logging.getLogger(constants.LOGGER_NAME)


@router.post("/agent-chat", tags=["AgentResource", "Command"])
async def chat_prompt_agent(prompt: ChatPromptAgentArgs) -> ConversationMessage:
    try:
        team = TeamService().get_team(prompt.team)
        team_member = team.get_member(prompt.role)
        response = await AgentService().chat_prompt_agent(
            agent=team_member.agent,
            identity=team_member.identity,
            team=prompt.team,
            role=prompt.role,
            history=prompt.history,
            message=prompt.message,
        )
        return ConversationMessage(
            sender=team_member.identity,
            message=response,
        )
    except (
        errors.TeamMemberNotFoundError,
        errors.TeamNotFoundError,
        errors.AgentNotFoundError,
    ) as e:
        logger.error(e.message)
        raise HTTPException(status_code=404, detail=e.message)
    except errors.AgentNotReadyError as e:
        logger.error(e.message)
        raise HTTPException(status_code=404, detail=e.message)
