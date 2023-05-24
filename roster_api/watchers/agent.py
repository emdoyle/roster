from typing import Callable, Optional

from roster_api import errors
from roster_api.watchers.base import BaseWatcher
from roster_api.watchers.etcd import EtcdResourceWatcher

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

    def _handle_event(self, event):
        # Process event before listeners receive it
        print(f"(agent) Received event: {event}")
        listeners = self.listeners.copy()
        for listener in listeners:
            try:
                listener(event)
            except errors.ListenerDisconnectedError:
                self.listeners.remove(listener)
            except Exception as e:
                # TODO: Log error
                print(f"(agent) Error in listener {listener}: {e}")

    def watch(self):
        self._watcher.watch()

    def start(self):
        self._watcher.start()

    def stop(self):
        self._watcher.stop()

    def add_listener(self, listener: Callable):
        self.listeners.append(listener)

    def remove_listener(self, listener: Callable):
        self.listeners.remove(listener)
