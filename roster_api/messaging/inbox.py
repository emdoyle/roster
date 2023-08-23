from typing import Optional

from roster_api import errors
from roster_api.messaging.rabbitmq import RabbitMQClient, get_rabbitmq
from roster_api.models.workflow import WorkflowActionTriggerPayload, WorkflowMessage
from roster_api.services.team import TeamService


class AgentInbox:
    def __init__(
        self,
        name: str,
        namespace: str = "default",
        rmq_client: Optional[RabbitMQClient] = None,
    ):
        self.name = name
        self.namespace = namespace
        self.rmq_client: RabbitMQClient = rmq_client or get_rabbitmq()

    @classmethod
    def from_role(
        cls, team: str, role: str, namespace: str = "default", **init_kwargs
    ) -> "AgentInbox":
        team_resource = TeamService().get_team(team, namespace=namespace)
        team_members = team_resource.spec.members
        role_member = team_members.get(role)
        if not role_member:
            raise errors.AgentNotFoundError()
        return cls(name=role_member.agent, namespace=namespace, **init_kwargs)

    @property
    def queue_name(self) -> str:
        return f"{self.namespace}:actor:agent:{self.name}"

    async def trigger_action(
        self, workflow_name: str, record_id: str, payload: WorkflowActionTriggerPayload
    ):
        message = WorkflowMessage(
            id=record_id,
            workflow=workflow_name,
            kind=WorkflowActionTriggerPayload.KEY,
            data=payload.dict(),
        )
        await self.rmq_client.publish_json(self.queue_name, message.dict())
