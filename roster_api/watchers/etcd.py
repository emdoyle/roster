import threading
from typing import Callable, Optional

import etcd3
from roster_api import settings

from ..db.etcd import wait_for_etcd
from .base import BaseWatcher


class EtcdResourceWatcher(BaseWatcher):
    def __init__(
        self,
        resource_prefix: str,
        listeners: Optional[list[Callable]] = None,
        client: Optional[etcd3.Etcd3Client] = None,
    ):
        self.resource_prefix = resource_prefix
        self.listeners = listeners or []
        self.client = client or etcd3.Etcd3Client(
            host=settings.ETCD_HOST, port=settings.ETCD_PORT
        )
        self.cancel = None
        self.thread = None

    def watch(self):
        wait_for_etcd(self.client)

        events_iterator, cancel = self.client.watch_prefix(self.resource_prefix)
        self.cancel = cancel
        for event in events_iterator:
            print(f"(etcd) Received event: {event}")
            for listener in self.listeners:
                try:
                    listener(event)
                except Exception as e:
                    # TODO: log error
                    print(f"(etcd) Error in listener {listener}: {e}")

    def start(self):
        if self.thread is not None:
            raise RuntimeError("Watcher already running")
        self.thread = threading.Thread(target=self.watch)
        self.thread.start()

    def stop(self):
        if self.thread is None or self.cancel is None:
            raise RuntimeError("Watcher not running")
        self.cancel()
        self.cancel = None
        self.thread.join()
        self.thread = None

    def add_listener(self, listener: Callable):
        self.listeners.append(listener)
