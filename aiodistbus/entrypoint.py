from collections import deque
from typing import Union, Callable, Coroutine, Type, TypeVar, Any, Optional, Literal, Dict

from .eventbus import EventBus
from .protocols import Event, OnHandler

T = TypeVar("T")

class EntryPoint:
    
    def __init__(self, id: str):

        # Parameters
        self.id = id

        # State information
        self._mode: Optional[Literal['local', 'remote']] = None
        self._handlers: Dict[str, OnHandler]
        self._received: deque[str] = deque(maxlen=10)

        # Local mode
        self._bus: Optional[EventBus] = None

        # Remote mode
        self._url: Optional[str] = None

    @property
    def handlers(self):
        ...

    async def _update_handlers(self):
        if self._mode == 'local':
            for k, self._handlers in self._handlers.items():
                ...
        elif self._mode == 'remote':
            ...
        else:
            raise Exception("EntryPoint is not connected to an EventBus")

    async def _emit(self, event: Event):
        ...

    ####################################################################################################################
    # Public API
    ####################################################################################################################

    async def local_subscribe(self, bus: EventBus):
        assert self._mode is None
        self._mode = 'local'
        self._bus = bus
        await self._update_handlers()

    async def subscribe(self, ip: str, port: int):
        assert self._mode is None
        self._mode = 'remote'
        await self._update_handlers()

    async def unsubscribe(self):
        ...

    async def on(self, event_type: str, handler: Union[Callable, Coroutine], dataclass: Type["T"]):
        # Keep record of handlers
        on_handler = OnHandler(event_type, handler, dataclass)
        self._handlers[event_type] = on_handler

        # Let the eventbus know about the handler
        if self._mode is not None:
            await self._update_handlers()

    async def emit(self, event_type: str, data: Any) -> Event:
        assert self._mode is not None, "EntryPoint is not connected to an EventBus"
        event = Event(event_type, data)
        await self._emit(event)
        return event

    async def extend(self, event_type: str, bus: EventBus, dataclass: Type["T"]):
        assert self._mode is not None, "EntryPoint is not connected to an EventBus"
        on_handler = OnHandler(event_type, bus.emit, dataclass)
        self._handlers[event_type] = on_handler
        
        # Let the eventbus know about the handler
        await self._update_handlers()
