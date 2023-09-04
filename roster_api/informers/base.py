from abc import ABC, abstractmethod
from typing import Callable, Generic, TypeVar

E = TypeVar("E")
T = TypeVar("T")


class Informer(ABC, Generic[T, E]):
    @abstractmethod
    async def setup(self):
        """setup informer -- called once on startup to establish listeners on remote data source"""

    @abstractmethod
    async def add_listener(self, listener: Callable[[E], None]):
        """add listener which receives objects on CRUD operations"""

    @abstractmethod
    async def remove_listener(self, listener: Callable[[E], None]):
        """remove listener"""

    @abstractmethod
    def list_resources(self) -> list[T]:
        """list all objects"""

    @abstractmethod
    async def teardown(self):
        """teardown informer -- release listeners on remote data sources"""
