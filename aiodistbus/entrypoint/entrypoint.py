import asyncio
import logging
from typing import (
    Any,
    Optional,
)

from ..eventbus import EventBus
from ..protocols import Event
from .aentrypoint import AEntryPoint

logger = logging.getLogger("aiodistbus")


class EntryPoint(AEntryPoint):
    def __init__(self, block: bool = True):
        super().__init__()

        self.block = block
        self._bus: Optional[EventBus] = None

    async def _update_handlers(
        self, event_type: Optional[str] = None, remove: bool = False
    ):
        if self._bus is None:
            return

        if remove and event_type:
            await self._bus._off(self.id, event_type)

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
        """Connect to a bus

        Args:
            bus (EventBus): EventBus to connect to

        """
        # Add bus and default handlers
        self._bus = bus
        await self.on("aiodistbus.eventbus.close", self.close)
        await self._update_handlers()

    async def emit(
        self, event_type: str, data: Any, id: Optional[str] = None
    ) -> Optional[Event]:
        """Emit an event

        Args:
            event_type (str): Event type
            data (Any): Data to send
            id (Optional[str], optional): Event ID. Defaults to None.

        Returns:
            Event: Event object

        """
        if self._bus is None:
            logger.error("aiodistbus: Not connected to a bus")
            return None

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
        """Close the entrypoint"""
        if self._bus:
            self._bus._remove(self.id)
            self._bus = None
