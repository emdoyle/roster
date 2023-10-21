import json
import logging
from typing import Type, TypeVar

import pydantic
from pydantic import BaseModel
from code_index import constants, errors

logger = logging.getLogger(constants.LOGGER_NAME)


def serialize(model: BaseModel) -> bytes:
    return json.dumps(model.json()).encode("utf-8")


T = TypeVar("T", bound=BaseModel)


def deserialize_from_etcd(model: Type[T], data: bytes) -> T:
    try:
        # SSE data from etcd event stream is double-encoded
        return model(**json.loads(json.loads(data.decode("utf-8"))))
    except (
        pydantic.ValidationError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as e:
        logger.error(
            "Failed to deserialize data from etcd for class: %s", model.__name__
        )
        raise errors.DeserializationError(
            "Could not deserialize data from etcd."
        ) from e
