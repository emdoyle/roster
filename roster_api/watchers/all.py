from roster_api.watchers.base import BaseWatcher

ACTIVE_WATCHERS: list[BaseWatcher] = []


def setup_watchers():
    from .resource import get_resource_watcher

    resource_watcher = get_resource_watcher()
    resource_watcher.start()

    global ACTIVE_WATCHERS
    ACTIVE_WATCHERS = [resource_watcher]


def teardown_watchers():
    global ACTIVE_WATCHERS
    for watcher in ACTIVE_WATCHERS:
        watcher.stop()
    ACTIVE_WATCHERS = []
