import asyncio
import uuid
from abc import ABC, abstractmethod
from collections import deque
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Optional,
    Type,
    Union,
)

from .eventbus import EventBus
from .protocols import Event, OnHandler


class AEntryPoint(ABC):
    def __init__(self):

        # State information
        self.id = str(uuid.uuid4())
        self._handlers: Dict[str, OnHandler] = {}
        self._received: deque[str] = deque(maxlen=10)

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

    # @abstractmethod
    async def close(self):
        ...


class DEntryPoint(AEntryPoint):
    ...


class EntryPoint(AEntryPoint):
    def __init__(self, block: bool = True):
        super().__init__()

        self.block = block
        self._bus: Optional[EventBus] = None

    async def _update_handlers(self):
        if self._bus is None:
            return
        for handler in self._handlers.values():
            await self._bus.on(self.id, handler)

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

    ####################################################################################################################
    ## PUBLIC API
    ####################################################################################################################

    async def connect(self, bus: EventBus):
        self._bus = bus
        await self._update_handlers()

    async def on(self, event_type: str, handler: Callable, dataclass: Type):
        wrapped_handler = self._wrapper(handler)
        on_handler = OnHandler(event_type, wrapped_handler, dataclass)
        self._handlers[event_type] = on_handler
        await self._update_handlers()

    async def emit(self, event_type: str, data: Any) -> Event:
        event = Event(event_type, data)
        if self.block:
            await self._bus.emit(event)
        else:
            asyncio.create_task(self._bus.emit(event))
        return event
