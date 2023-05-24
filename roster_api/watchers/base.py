from abc import ABC, abstractmethod


class BaseWatcher(ABC):
    @abstractmethod
    def watch(self):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def add_listener(self, listener):
        pass
