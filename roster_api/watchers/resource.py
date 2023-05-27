import json
import logging
from typing import TYPE_CHECKING, Callable, Optional

from roster_api import constants, errors
from roster_api.events.spec import DeleteResourceEvent, PutResourceEvent, ResourceEvent
from roster_api.resources.base import resource_type_from_etcd_prefix
from roster_api.watchers.base import BaseWatcher
from roster_api.watchers.etcd import EtcdResourceWatcher

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


class ResourceWatcher(BaseWatcher):
    KEY_PREFIX = "/registry"

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
                    try:
                        prev_resource = json.loads(
                            json.loads(prev_value.decode("utf-8"))
                        )
                    except json.JSONDecodeError as e:
                        logger.warning(
                            "(resource) Error decoding prev_value in etcd event: %s", e
                        )

                if prev_resource is not None:
                    # This is an update event
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
                    spec_changed=spec_changed,
                    status_changed=status_changed,
                )

            elif "Delete" in str(event.__class__):
                return DeleteResourceEvent(
                    resource_type=resource_type, namespace=namespace, name=name
                )
        except Exception as e:
            logger.debug("(resource) Error processing event: %s", e)
            raise errors.InvalidEventError(f"Invalid event: {event}") from e

    def _handle_event(self, event: "etcd3.events.Event"):
        logger.debug("(resource) Received event: %s", event)
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
                logger.exception("(resource) Error in listener %s: %s", listener, e)

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
        self.listeners.remove(listener)
