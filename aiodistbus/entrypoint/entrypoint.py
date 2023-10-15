import asyncio
from typing import (
    Any,
    Callable,
    Optional,
    Type,
)

from ..eventbus import EventBus
from ..protocols import Event, OnHandler
from .aentrypoint import AEntryPoint


class EntryPoint(AEntryPoint):
    def __init__(self, block: bool = True):
        super().__init__()

        self.block = block
        self._bus: Optional[EventBus] = None

    async def _update_handlers(self):
        if self._bus is None:
            return
        for handler in self._handlers.values():
            await self._bus._on(self.id, handler)

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
            await self._bus._emit(event)
        else:
            asyncio.create_task(self._bus._emit(event))
        return event

    async def close(self):
        if self._bus:
            self._bus._remove(self.id)
