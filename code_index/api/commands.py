import logging

from fastapi import APIRouter, HTTPException, Request
from code_index import constants, errors
from code_index.constants import EXECUTION_ID_HEADER, EXECUTION_TYPE_HEADER
from code_index.models.chat import ChatPromptAgentArgs, ConversationMessage
from code_index.models.workflow import InitiateWorkflowArgs
from code_index.services.agent import AgentService
from code_index.services.team import TeamService
from code_index.services.workflow import WorkflowService

router = APIRouter()

logger = logging.getLogger(constants.LOGGER_NAME)


@router.post("/agent-chat", tags=["AgentResource", "Command"])
async def chat_prompt_agent(
    request: Request, prompt: ChatPromptAgentArgs
) -> ConversationMessage:
    execution_id = request.headers.get(EXECUTION_ID_HEADER, "")
    execution_type = request.headers.get(EXECUTION_TYPE_HEADER, "")

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
            execution_id=execution_id,
            execution_type=execution_type,
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


@router.post("/initiate-workflow", tags=["WorkflowResource", "Command"])
async def initiate_workflow(args: InitiateWorkflowArgs):
    try:
        return await WorkflowService().initiate_workflow(
            workflow_name=args.workflow, inputs=args.inputs
        )
    except errors.WorkflowNotFoundError as e:
        logger.error(e.message)
        raise HTTPException(status_code=404, detail=e.message)
    except errors.WorkflowNotReadyError as e:
        logger.error(e.message)
        raise HTTPException(status_code=404, detail=e.message)
    except errors.RosterAPIError as e:
        logger.error(e.message)
        raise HTTPException(status_code=500, detail=e.message)
