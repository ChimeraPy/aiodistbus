import logging
from abc import ABC, abstractmethod
from typing import Dict, Type

from ..protocols import Event, Subscriptions

logger = logging.getLogger(__name__)


class AEventBus(ABC):
    def __init__(self):

        # State information
        self._running = False
        self._subs: Dict[str, Dict[str, Subscriptions]] = {}

    @property
    def running(self):
        return self._running

    @abstractmethod
    async def _on(self, event_type: str, dtype: Type):
        ...

    @abstractmethod
    async def _emit(self, event: Event):
        ...

    @abstractmethod
    async def forward(self, event_type: str):
        ...

    # @abstractmethod
    async def deforward(self, event_type: str):
        ...

    @abstractmethod
    async def close(self):
        ...
