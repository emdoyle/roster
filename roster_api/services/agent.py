import logging
from typing import Optional

import aiohttp
import etcd3
import pydantic
from roster_api import constants, errors
from roster_api.constants import EXECUTION_ID_HEADER, EXECUTION_TYPE_HEADER
from roster_api.db.etcd import get_etcd_client
from roster_api.events.status import StatusEvent
from roster_api.models.agent import AgentResource, AgentSpec, AgentStatus
from roster_api.models.chat import ConversationMessage
from roster_api.util.serialization import deserialize_from_etcd, serialize

logger = logging.getLogger(constants.LOGGER_NAME)


class AgentService:
    KEY_PREFIX = "/resources/agents"
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
            agent_key, serialize(agent_resource)
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
        return deserialize_from_etcd(AgentResource, agent_data)

    def list_agents(self, namespace: str = DEFAULT_NAMESPACE) -> list[AgentResource]:
        agent_key = self._get_agent_key("", namespace)
        agent_data = self.etcd_client.get_prefix(agent_key)
        return [deserialize_from_etcd(AgentResource, data) for data, _ in agent_data]

    def update_agent(
        self, agent: AgentSpec, namespace: str = DEFAULT_NAMESPACE
    ) -> AgentResource:
        agent_key = self._get_agent_key(agent.name, namespace)
        agent_resource = self.get_agent(agent.name, namespace)
        agent_resource.spec = agent
        self.etcd_client.put(agent_key, serialize(agent_resource))
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
        agent: str,
        identity: str,
        team: str,
        role: str,
        history: list[ConversationMessage],
        message: ConversationMessage,
        execution_id: str = "",
        execution_type: str = "",
        namespace: str = DEFAULT_NAMESPACE,
    ) -> str:
        agent_resource = self.get_agent(agent)
        agent_host = agent_resource.status.host_ip
        if not agent_host:
            raise errors.AgentNotReadyError(agent=agent)

        try:
            headers = {}
            if execution_id:
                headers[EXECUTION_ID_HEADER] = execution_id
            if execution_type:
                headers[EXECUTION_TYPE_HEADER] = execution_type
            async with aiohttp.ClientSession() as session:
                # TODO: https, fix host, auth, configurable port, namespace etc.
                payload = {
                    "identity": identity,
                    "team": team,
                    "role": role,
                    "history": [_message.dict() for _message in history],
                    "message": message.dict(),
                }
                async with session.post(
                    f"http://host.docker.internal:7890/v0.1/agent/{agent}/chat",
                    json=payload,
                    headers=headers,
                ) as resp:
                    return await resp.text()
        except aiohttp.ClientError as e:
            logger.error(e)
            raise errors.AgentNotReadyError(agent=agent) from e

    def _handle_agent_status_put(self, status_update: StatusEvent):
        agent_key = self._get_agent_key(status_update.name)
        agent_data, _ = self.etcd_client.get(agent_key)
        if not agent_data:
            raise errors.AgentNotFoundError(agent=status_update.name)
        try:
            updated_status = AgentStatus(
                host_ip=status_update.host_ip, **status_update.status
            )
        except pydantic.ValidationError as e:
            raise errors.InvalidEventError(event=status_update) from e
        agent_resource = deserialize_from_etcd(AgentResource, agent_data)
        agent_resource.status = updated_status
        self.etcd_client.put(agent_key, serialize(agent_resource))
        logger.debug("Updated Agent %s status.", status_update.name)

    def _handle_agent_status_delete(self, status_update: StatusEvent):
        agent_key = self._get_agent_key(status_update.name)
        agent_data, _ = self.etcd_client.get(agent_key)
        if not agent_data:
            logger.debug("Agent %s already deleted.", status_update.name)
            return
        agent_resource = deserialize_from_etcd(AgentResource, agent_data)
        agent_resource.status = AgentStatus(name=status_update.name, status="deleted")
        self.etcd_client.put(agent_key, serialize(agent_resource))
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
