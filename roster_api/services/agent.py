import logging
from typing import Optional

import aiohttp
import etcd3
import pydantic
from roster_api import constants, errors
from roster_api.db.etcd import get_etcd_client
from roster_api.events.status import StatusEvent
from roster_api.models.agent import AgentResource, AgentSpec, AgentStatus
from roster_api.models.chat import ConversationMessage

logger = logging.getLogger(constants.LOGGER_NAME)


class AgentService:
    KEY_PREFIX = "/registry/agents"
    DEFAULT_NAMESPACE = "default"

    def __init__(self, etcd_client: Optional[etcd3.Etcd3Client] = None):
        self.etcd_client: etcd3.Etcd3Client = etcd_client or get_etcd_client()

    def _get_agent_key(
        self, agent_name: str, namespace: str = DEFAULT_NAMESPACE
    ) -> str:
        return f"{self.KEY_PREFIX}/{namespace}/{agent_name}"

    def create_agent(
        self, agent: AgentSpec, namespace: str = DEFAULT_NAMESPACE
    ) -> AgentResource:
        agent_key = self._get_agent_key(agent.name, namespace)
        agent_resource = AgentResource.initial_state(spec=agent)
        created = self.etcd_client.put_if_not_exists(
            agent_key, agent_resource.serialize()
        )
        if not created:
            raise errors.AgentAlreadyExistsError(agent=agent)
        logger.debug("Created Agent %s", agent.name)
        return agent_resource

    def get_agent(self, name: str, namespace: str = DEFAULT_NAMESPACE) -> AgentResource:
        agent_key = self._get_agent_key(name, namespace)
        agent_data, _ = self.etcd_client.get(agent_key)
        if not agent_data:
            raise errors.AgentNotFoundError(agent=name)
        return AgentResource.deserialize_from_etcd(agent_data)

    def list_agents(self, namespace: str = DEFAULT_NAMESPACE) -> list[AgentResource]:
        agent_key = self._get_agent_key("", namespace)
        agent_data = self.etcd_client.get_prefix(agent_key)
        return [AgentResource.deserialize_from_etcd(data) for data, _ in agent_data]

    def update_agent(
        self, agent: AgentSpec, namespace: str = DEFAULT_NAMESPACE
    ) -> AgentResource:
        agent_key = self._get_agent_key(agent.name, namespace)
        agent_resource = self.get_agent(agent.name, namespace)
        agent_resource.spec = agent
        self.etcd_client.put(agent_key, agent_resource.serialize())
        logger.debug(f"Updated Agent {agent.name}.")
        return agent_resource

    def delete_agent(self, name: str, namespace: str = DEFAULT_NAMESPACE) -> bool:
        agent_key = self._get_agent_key(name, namespace)
        deleted = self.etcd_client.delete(agent_key)
        if deleted:
            logger.debug(f"Deleted Agent {name}.")
        return deleted

    async def chat_prompt_agent(
        self,
        name: str,
        history: list[ConversationMessage],
        message: ConversationMessage,
        namespace: str = DEFAULT_NAMESPACE,
    ):
        agent = self.get_agent(name)
        agent_host = agent.status.host_ip
        if not agent_host:
            raise errors.AgentNotReadyError(agent=name)

        try:
            async with aiohttp.ClientSession() as session:
                # TODO: https, fix host, auth, configurable port, namespace etc.
                async with session.post(
                    f"http://host.docker.internal:7890/v0.1/messaging/agent/{name}/chat",
                    json={
                        "history": [_message.dict() for _message in history],
                        "message": message.dict(),
                    },
                ) as resp:
                    return await resp.json()
        except aiohttp.ClientError as e:
            logger.error(e)
            raise errors.AgentNotReadyError(agent=name) from e

    def _handle_agent_status_put(self, status_update: StatusEvent):
        agent_key = self._get_agent_key(status_update.name)
        agent_data, _ = self.etcd_client.get(agent_key)
        if not agent_data:
            raise errors.AgentNotFoundError(agent=status_update.name)
        agent_resource = AgentResource.deserialize_from_etcd(agent_data)
        try:
            updated_status = AgentStatus(
                host_ip=status_update.host_ip, **status_update.status
            )
        except (TypeError, pydantic.ValidationError) as e:
            raise errors.InvalidEventError(event=status_update) from e
        agent_resource.status = updated_status
        self.etcd_client.put(agent_key, agent_resource.serialize())
        logger.debug("Updated Agent %s status.", status_update.name)

    def _handle_agent_status_delete(self, status_update: StatusEvent):
        agent_key = self._get_agent_key(status_update.name)
        agent_data, _ = self.etcd_client.get(agent_key)
        if not agent_data:
            logger.debug("Agent %s already deleted.", status_update.name)
            return
        agent_resource = AgentResource.deserialize_from_etcd(agent_data)
        agent_resource.status = AgentStatus(name=status_update.name, status="deleted")
        self.etcd_client.put(agent_key, agent_resource.serialize())
        logger.debug("Deleted Agent %s status.", status_update.name)

    def handle_agent_status_update(self, status_update: StatusEvent):
        if status_update.event_type == "PUT":
            self._handle_agent_status_put(status_update)
        elif status_update.event_type == "DELETE":
            self._handle_agent_status_delete(status_update)
        else:
            logger.warning(
                "Received status update for unknown event type: %s",
                status_update.event_type,
            )
