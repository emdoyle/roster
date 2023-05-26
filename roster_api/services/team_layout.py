import logging
from typing import Optional

import etcd3
from roster_api import constants, errors
from roster_api.db.etcd import get_etcd_client
from roster_api.models.team_layout import TeamLayoutResource, TeamLayoutSpec

logger = logging.getLogger(constants.LOGGER_NAME)


class TeamLayoutService:
    KEY_PREFIX = "/registry/team-layouts"
    DEFAULT_NAMESPACE = "default"

    def __init__(self, etcd_client: Optional[etcd3.Etcd3Client] = None):
        self.etcd_client: etcd3.Etcd3Client = etcd_client or get_etcd_client()

    def _get_team_layout_key(
        self, team_layout_name: str, namespace: str = DEFAULT_NAMESPACE
    ) -> str:
        return f"{self.KEY_PREFIX}/{namespace}/{team_layout_name}"

    def create_team_layout(
        self, team_layout: TeamLayoutSpec, namespace: str = DEFAULT_NAMESPACE
    ) -> TeamLayoutResource:
        team_layout_key = self._get_team_layout_key(team_layout.name, namespace)
        team_layout_resource = TeamLayoutResource.initial_state(spec=team_layout)
        created = self.etcd_client.put_if_not_exists(
            team_layout_key, team_layout_resource.serialize()
        )
        if not created:
            raise errors.TeamLayoutAlreadyExistsError(team_layout=team_layout)
        logger.debug("Created TeamLayout %s", team_layout.name)
        return team_layout_resource

    def get_team_layout(
        self, name: str, namespace: str = DEFAULT_NAMESPACE
    ) -> TeamLayoutResource:
        team_layout_key = self._get_team_layout_key(name, namespace)
        team_layout_data, _ = self.etcd_client.get(team_layout_key)
        if not team_layout_data:
            raise errors.TeamLayoutNotFoundError(team_layout=name)
        return TeamLayoutResource.deserialize_from_etcd(team_layout_data)

    def list_team_layouts(
        self, namespace: str = DEFAULT_NAMESPACE
    ) -> list[TeamLayoutResource]:
        team_layout_key = self._get_team_layout_key("", namespace)
        team_layout_data = self.etcd_client.get_prefix(team_layout_key)
        return [
            TeamLayoutResource.deserialize_from_etcd(data)
            for data, _ in team_layout_data
        ]

    def update_team_layout(
        self, team_layout: TeamLayoutSpec, namespace: str = DEFAULT_NAMESPACE
    ) -> TeamLayoutResource:
        team_layout_key = self._get_team_layout_key(team_layout.name, namespace)
        team_layout_resource = self.get_team_layout(team_layout.name, namespace)
        team_layout_resource.spec = team_layout
        self.etcd_client.put(team_layout_key, team_layout_resource.serialize())
        logger.debug(f"Updated TeamLayout {team_layout.name}.")
        return team_layout_resource

    def delete_team_layout(self, name: str, namespace: str = DEFAULT_NAMESPACE) -> bool:
        team_layout_key = self._get_team_layout_key(name, namespace)
        deleted = self.etcd_client.delete(team_layout_key)
        if deleted:
            logger.debug(f"Deleted TeamLayout {name}.")
        return deleted
