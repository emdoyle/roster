import logging
from typing import Optional

import etcd3
from roster_api import constants, errors
from roster_api.db.etcd import get_etcd_client
from roster_api.models.team import TeamResource, TeamSpec
from roster_api.util.serialization import deserialize_from_etcd, serialize

logger = logging.getLogger(constants.LOGGER_NAME)


class TeamService:
    KEY_PREFIX = "/resources/teams"
    DEFAULT_NAMESPACE = "default"

    def __init__(self, etcd_client: Optional[etcd3.Etcd3Client] = None):
        self.etcd_client: etcd3.Etcd3Client = etcd_client or get_etcd_client()

    def _get_team_key(self, team_name: str, namespace: str = DEFAULT_NAMESPACE) -> str:
        return f"{self.KEY_PREFIX}/{namespace}/{team_name}"

    def create_team(
        self, team: TeamSpec, namespace: str = DEFAULT_NAMESPACE
    ) -> TeamResource:
        team_key = self._get_team_key(team.name, namespace)
        team_resource = TeamResource.initial_state(spec=team)
        logger.debug(
            "Assuming members are accurately specified for Team %s.", team.name
        )
        team_resource.status.members = team_resource.spec.members
        created = self.etcd_client.put_if_not_exists(team_key, serialize(team_resource))
        if not created:
            raise errors.TeamAlreadyExistsError(team=team)
        logger.debug("Created Team %s", team.name)
        return team_resource

    def get_team(self, name: str, namespace: str = DEFAULT_NAMESPACE) -> TeamResource:
        team_key = self._get_team_key(name, namespace)
        team_data, _ = self.etcd_client.get(team_key)
        if not team_data:
            raise errors.TeamNotFoundError(team=name)
        return deserialize_from_etcd(TeamResource, team_data)

    def list_teams(self, namespace: str = DEFAULT_NAMESPACE) -> list[TeamResource]:
        team_key = self._get_team_key("", namespace)
        team_data = self.etcd_client.get_prefix(team_key)
        return [deserialize_from_etcd(TeamResource, data) for data, _ in team_data]

    def update_team(
        self, team: TeamSpec, namespace: str = DEFAULT_NAMESPACE
    ) -> TeamResource:
        team_key = self._get_team_key(team.name, namespace)
        team_resource = self.get_team(team.name, namespace)
        team_resource.spec = team
        logger.debug(
            "Assuming members are accurately specified for Team %s.", team.name
        )
        team_resource.status.members = team_resource.spec.members
        self.etcd_client.put(team_key, serialize(team_resource))
        logger.debug(f"Updated Team {team.name}.")
        return team_resource

    def delete_team(self, name: str, namespace: str = DEFAULT_NAMESPACE) -> bool:
        team_key = self._get_team_key(name, namespace)
        deleted = self.etcd_client.delete(team_key)
        if deleted:
            logger.debug(f"Deleted Team {name}.")
        return deleted
