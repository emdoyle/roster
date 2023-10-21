import json
import logging
from typing import TYPE_CHECKING, Callable, Optional

from code_index import constants, errors
from code_index.events.resource import (
    DeleteResourceEvent,
    PutResourceEvent,
    ResourceEvent,
)
from code_index.resources.base import resource_type_from_etcd_prefix
from code_index.watchers.base import BaseWatcher
from code_index.watchers.etcd import EtcdResourceWatcher

if TYPE_CHECKING:
    import etcd3

logger = logging.getLogger(constants.LOGGER_NAME)

RESOURCE_WATCHER: Optional["ResourceWatcher"] = None


def get_resource_watcher() -> "ResourceWatcher":
    global RESOURCE_WATCHER
    if RESOURCE_WATCHER is not None:
        return RESOURCE_WATCHER

    RESOURCE_WATCHER = ResourceWatcher()
    return RESOURCE_WATCHER


# TODO: might make sense to allow filtering at the connection level
class ResourceWatcher(BaseWatcher):
    KEY_PREFIX = "/resources"

    def __init__(self, listeners: Optional[list[Callable]] = None):
        self.listeners = listeners or []
        self._watcher = EtcdResourceWatcher(
            resource_prefix=self.KEY_PREFIX, listeners=[self._handle_event]
        )

    @classmethod
    def _process_event(cls, event: "etcd3.events.Event") -> Optional[ResourceEvent]:
        try:
            key = event.key.decode()[len(cls.KEY_PREFIX) + 1 :]
            resource_prefix, namespace, name = key.split("/")
            resource_type = resource_type_from_etcd_prefix(resource_prefix)

            if "Put" in str(event.__class__):
                # SSE events are double-encoded
                resource = json.loads(json.loads(event.value.decode("utf-8")))
                prev_value = getattr(event, "prev_value", None)
                prev_resource = None
                if prev_value:
                    # This is an update event
                    prev_resource = json.loads(
                        json.loads(event.prev_value.decode("utf-8"))
                    )
                    spec_changed = resource["spec"] != prev_resource["spec"]
                    status_changed = resource["status"] != prev_resource["status"]
                else:
                    # This is a create event
                    spec_changed = True
                    status_changed = True

                return PutResourceEvent(
                    resource_type=resource_type,
                    namespace=namespace,
                    name=name,
                    resource=resource,
                    previous_resource=prev_resource,
                    spec_changed=spec_changed,
                    status_changed=status_changed,
                )

            elif "Delete" in str(event.__class__):
                prev_resource = json.loads(json.loads(event.prev_value.decode("utf-8")))
                return DeleteResourceEvent(
                    resource_type=resource_type,
                    namespace=namespace,
                    name=name,
                    resource=prev_resource,
                )
        except Exception as e:
            logger.debug("(resource) Error processing event: %s", e)
            raise errors.InvalidEventError(event=event) from e

    def _handle_event(self, event: "etcd3.events.Event"):
        logger.debug("(resource) Received event from etcd")
        try:
            event = self._process_event(event)
        except errors.InvalidEventError as e:
            logger.warning("Failed to process resource event from etcd: %s", e)
            return
        if event is None:
            return
        logger.debug("(resource) Sending resource event: %s", event)
        listeners = self.listeners.copy()
        for listener in listeners:
            try:
                listener(event)
            except errors.ListenerDisconnectedError:
                self.listeners.remove(listener)
            except Exception as e:
                logger.error("Error in resource listener %s", listener.__name__)
                logger.debug(
                    "(resource) Error in listener %s: %s", listener.__name__, e
                )

    def watch(self):
        self._watcher.watch()

    def start(self):
        self._watcher.start()
        logger.info("Starting resource watcher")

    def stop(self):
        self._watcher.stop()
        logger.info("Resource watcher stopped")

    def add_listener(self, listener: Callable):
        self.listeners.append(listener)

    def remove_listener(self, listener: Callable):
        if listener in self.listeners:
            self.listeners.remove(listener)