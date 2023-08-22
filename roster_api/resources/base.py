from enum import Enum


class ResourceType(Enum):
    Agent = "AGENT"
    Identity = "IDENTITY"
    Team = "TEAM"


etcd_prefixes = {
    ResourceType.Agent: "agents",
    ResourceType.Identity: "identities",
    ResourceType.Team: "teams",
}
resource_types_by_etcd_prefix = {v: k for k, v in etcd_prefixes.items()}


def resource_type_from_etcd_prefix(prefix: str) -> ResourceType:
    try:
        return resource_types_by_etcd_prefix[prefix]
    except KeyError:
        raise ValueError(f"Unknown resource for etcd prefix {prefix}")
