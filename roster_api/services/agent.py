import logging
from typing import Optional

import etcd3
from roster_api import constants, errors
from roster_api.db.etcd import get_etcd_client
from roster_api.models.agent import AgentResource, AgentSpec

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
