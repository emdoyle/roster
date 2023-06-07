import json
import logging

import pydantic
from pydantic import BaseModel, Field, constr
from roster_api import constants, errors
from roster_api.constants import API_VERSION

logger = logging.getLogger(constants.LOGGER_NAME)


class RosterResource(BaseModel):
    api_version: constr(regex="^v[0-9.]+$") = Field(
        default=API_VERSION, description="The api version."
    )
    kind: str = Field(description="The kind of resource.")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="The metadata of the agent."
    )

    class Config:
        validate_assignment = True

    def serialize(self) -> bytes:
        return json.dumps(self.json()).encode("utf-8")

    @classmethod
    def deserialize_from_etcd(cls, data: bytes) -> "RosterResource":
        try:
            # SSE data is double-encoded
            return cls(**json.loads(json.loads(data.decode("utf-8"))))
        except (
            pydantic.ValidationError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as e:
            logger.error(
                "Failed to deserialize data from etcd for class: %s", cls.__name__
            )
            raise errors.InvalidResourceError(
                "Could not deserialize resource from etcd."
            ) from e
