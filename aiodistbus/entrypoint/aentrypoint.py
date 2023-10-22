import asyncio
import uuid
from abc import ABC, abstractmethod
from collections import deque
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Type,
    Union,
)

from ..protocols import Event, OnHandler


class AEntryPoint(ABC):
    def __init__(self):

        # State information
        self.id = str(uuid.uuid4())
        self._handlers: Dict[str, OnHandler] = {}
        self._wildcards: Dict[str, OnHandler] = {}
        self._received: deque[str] = deque(maxlen=10)

    def _wrapper(self, handler: Callable) -> Callable:
        async def awrapper(event: Event):
            await handler(event.data)
            self._received.append(event.id)

        def wrapper(event: Event):
            handler(event.data)
            self._received.append(event.id)

        if asyncio.iscoroutinefunction(handler):
            return awrapper
        else:
            return wrapper

    @abstractmethod
    async def on(
        self, event_type: str, handler: Union[Callable, Coroutine], dataclass: Type
    ):
        ...

    @abstractmethod
    async def connect(self):
        ...

    @abstractmethod
    async def emit(self, event_type: str, data: Any) -> Event:
        ...

    @abstractmethod
    async def close(self):
        ...
