import logging
from typing import Optional

import aiohttp
from roster_api import constants, errors
from roster_api.models.task import TaskAssignment, TaskSpec
from roster_api.services.agent import AgentService
from roster_api.services.task import TaskService
from roster_api.services.team import TeamService

logger = logging.getLogger(constants.LOGGER_NAME)


class TaskExecutor:
    def __init__(
        self,
        task_service: Optional[TaskService] = None,
        team_service: Optional[TeamService] = None,
        agent_service: Optional[AgentService] = None,
    ):
        self.task_service = task_service or TaskService()
        self.team_service = team_service or TeamService()
        self.agent_service = agent_service or AgentService()

    async def _initiate_task(self, task: TaskSpec, assignment: TaskAssignment):
        # TODO: https, fix host, auth, configurable port, namespace etc.
        #   not static/classmethod because agent service would
        #   theoretically be needed for networking
        runtime_url = "http://host.docker.internal:7890"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{runtime_url}/v0.1/agent/{assignment.agent_name}/tasks",
                    json={
                        "task": task.name,
                        "description": task.description,
                        "assignment": assignment.dict(),
                    },
                    raise_for_status=True,
                ) as resp:
                    assert resp.status == 200
        except (AssertionError, aiohttp.ClientResponseError) as e:
            logger.error("Failed to assign task.")
            logger.debug("(task-exec) Failed to assign task %s", e.message)
            raise errors.RosterAPIError("Failed to assign task") from e
        except aiohttp.ClientError as e:
            logger.error("Failed to reach Roster runtime to assign task.")
            logger.debug("(task-exec) Failed to reach Roster runtime %s", e)
            raise errors.RosterAPIError("Failed to assign task") from e
        except Exception as e:
            logger.error("Failed to assign task.")
            logger.debug("(task-exec) Failed to assign task %s", e)
            raise errors.RosterAPIError("Failed to assign task") from e

    async def assign_task(self, task: TaskSpec) -> TaskAssignment:
        teams = self.team_service.list_teams()
        if not teams:
            raise errors.TeamNotFoundError()
        # TODO: arbitrary assignment
        team = teams[0]
        roles = team.spec.layout.non_manager_roles
        if not roles:
            raise errors.TeamRoleNotFoundError()
        role = list(roles)[0]
        member = team.spec.members.get(role)
        if not member:
            raise errors.TeamMemberNotFoundError()

        assignment = TaskAssignment(
            team_name=team.spec.name,
            role_name=role,
            identity_name=member.identity,
            agent_name=member.agent,
        )
        await self._initiate_task(task, assignment)
        return assignment

    async def cancel_task(self, name: str, agent_name: str, namespace: str = "default"):
        # TODO: https, fix host, auth, configurable port, namespace etc.
        #   not static/classmethod because agent service would
        #   theoretically be needed for networking
        runtime_url = "http://host.docker.internal:7890"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{runtime_url}/v0.1/agent/{agent_name}/tasks/{name}",
                    raise_for_status=True,
                ):
                    return
        except aiohttp.ClientResponseError as e:
            logger.error("Failed to cancel task.")
            logger.debug("(task-exec) Failed to cancel task %s", e.message)
            raise errors.RosterAPIError("Failed to cancel task") from e
        except aiohttp.ClientError as e:
            logger.error("Failed to reach Roster runtime to cancel task.")
            logger.debug("(task-exec) Failed to reach Roster runtime %s", e)
            raise errors.RosterAPIError("Failed to cancel task") from e
        except Exception as e:
            logger.error("Failed to cancel task.")
            logger.debug("(task-exec) Failed to cancel task %s", e)
            raise errors.RosterAPIError("Failed to cancel task") from e
