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

    async def _update_handlers(self, event_type: Optional[str] = None):
        if self._bus is None:
            return

        if event_type:
            if event_type in self._handlers:
                await self._bus._on(self.id, self._handlers[event_type])
            elif event_type in self._wildcards:
                await self._bus._on(self.id, self._wildcards[event_type])
        else:
            for handler in self._handlers.values():
                await self._bus._on(self.id, handler)
            for handler in self._wildcards.values():
                await self._bus._on(self.id, handler)

    ####################################################################################################################
    ## PUBLIC API
    ####################################################################################################################

    async def connect(self, bus: EventBus):
        # Add bus and default handlers
        self._bus = bus
        await self.on("eventbus.close", self.close)
        await self._update_handlers()

    async def on(
        self, event_type: str, handler: Callable, dtype: Optional[Type] = None
    ):

        # Track handlers (supporting wildcards)
        if "*" not in event_type:
            wrapped_handler = self._wrapper(handler)
            on_handler = OnHandler(event_type, wrapped_handler, dtype)
            self._handlers[event_type] = on_handler
        else:
            wrapped_handler = self._wrapper(handler, unpack=False)
            on_handler = OnHandler(event_type, wrapped_handler, dtype)
            self._wildcards[event_type] = on_handler

        await self._update_handlers(event_type)

    async def emit(self, event_type: str, data: Any, id: Optional[str] = None) -> Event:

        # Constructing event
        if id:
            event = Event(event_type, data, id)
        else:
            event = Event(event_type, data)

        if self.block:
            await self._bus._emit(event)
        else:
            asyncio.create_task(self._bus._emit(event))
        return event

    async def close(self):
        if self._bus:
            self._bus._remove(self.id)
            self._bus = None
