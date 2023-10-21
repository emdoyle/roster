import json
import logging

import pydantic
from pydantic import BaseModel, Field, constr
from code_index import constants, errors
from code_index.constants import API_VERSION

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
