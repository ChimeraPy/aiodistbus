import asyncio
from abc import ABC, abstractmethod
from collections import deque
from typing import Union, Callable, Coroutine, Type, TypeVar, Any, Optional, Literal, Dict

from .eventbus import EventBus
from .protocols import Event, OnHandler

class AEntryPoint(ABC):
    
    def __init__(self):

        # State information
        self._handlers: Dict[str, OnHandler] = {}
        self._received: deque[str] = deque(maxlen=10)
   
    @abstractmethod
    async def on(self, event_type: str, handler: Union[Callable, Coroutine], dataclass: Type):
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

    def _update_handlers(self):
        ...

    ####################################################################################################################
    ## PUBLIC API
    ####################################################################################################################
    
    async def connect(self, bus: EventBus):
        self._bus = bus
        self._update_handlers()

    async def on(self, event_type: str, handler: Union[Callable, Coroutine], dataclass: Type):
        on_handler = OnHandler(event_type, handler, dataclass)
        self._handlers[event_type] = on_handler
        self._update_handlers()

    async def emit(self, event_type: str, data: Any) -> Event:
        event = Event(event_type, data)
        if self.block:
            await self._bus.emit(event)
        else:
            asyncio.create_task(self._bus.emit(event))
        return event
