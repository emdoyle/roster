from roster_api.watchers.base import BaseWatcher

ACTIVE_WATCHERS: list[BaseWatcher] = []


def setup_watchers():
    from .agent import get_agent_resource_watcher

    agent_watcher = get_agent_resource_watcher()
    agent_watcher.start()

    global ACTIVE_WATCHERS
    ACTIVE_WATCHERS = [agent_watcher]


def teardown_watchers():
    global ACTIVE_WATCHERS
    for watcher in ACTIVE_WATCHERS:
        watcher.stop()
    ACTIVE_WATCHERS = []
