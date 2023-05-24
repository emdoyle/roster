import logging
from typing import TYPE_CHECKING, Callable, Optional

from roster_api import constants, errors
from roster_api.events.agent import (
    AgentSpecEvent,
    DeleteAgentSpecEvent,
    PutAgentSpecEvent,
)
from roster_api.models.agent import AgentSpec
from roster_api.watchers.base import BaseWatcher
from roster_api.watchers.etcd import EtcdResourceWatcher

if TYPE_CHECKING:
    import etcd3

logger = logging.getLogger(constants.LOGGER_NAME)

AGENT_RESOURCE_WATCHER: Optional["AgentResourceWatcher"] = None


def get_agent_resource_watcher() -> "AgentResourceWatcher":
    global AGENT_RESOURCE_WATCHER
    if AGENT_RESOURCE_WATCHER is not None:
        return AGENT_RESOURCE_WATCHER

    AGENT_RESOURCE_WATCHER = AgentResourceWatcher()
    return AGENT_RESOURCE_WATCHER


class AgentResourceWatcher(BaseWatcher):
    KEY_PREFIX = "/registry/agents"

    def __init__(self, listeners: Optional[list[Callable]] = None):
        self.listeners = listeners or []
        self._watcher = EtcdResourceWatcher(
            resource_prefix=self.KEY_PREFIX, listeners=[self._handle_event]
        )

    @classmethod
    def _process_event(cls, event: "etcd3.events.Event") -> AgentSpecEvent:
        try:
            key = event.key.decode()[len(cls.KEY_PREFIX) + 1 :]
            namespace, name = key.split("/")
            if "Put" in str(event.__class__):
                return PutAgentSpecEvent(
                    namespace=namespace,
                    name=name,
                    spec=AgentSpec.parse_raw(event.value),
                )
            elif "Delete" in str(event.__class__):
                return DeleteAgentSpecEvent(namespace=namespace, name=name)
        except Exception as e:
            raise errors.InvalidEventError(f"Invalid event: {event}") from e

    def _handle_event(self, event: "etcd3.events.Event"):
        try:
            event = self._process_event(event)
        except errors.InvalidEventError as e:
            logger.debug(f"(agent) Error processing event: {e}")
            return
        logger.debug(f"(agent) Received event: {event}")
        listeners = self.listeners.copy()
        for listener in listeners:
            try:
                listener(event)
            except errors.ListenerDisconnectedError:
                self.listeners.remove(listener)
            except Exception as e:
                logger.exception(f"(agent) Error in listener {listener}: {e}")

    def watch(self):
        self._watcher.watch()

    def start(self):
        self._watcher.start()
        logger.info("Watching Agent resources")

    def stop(self):
        self._watcher.stop()
        logger.info("Agent watcher stopped")

    def add_listener(self, listener: Callable):
        self.listeners.append(listener)

    def remove_listener(self, listener: Callable):
        self.listeners.remove(listener)
