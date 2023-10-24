import asyncio
import logging
from collections import defaultdict
from typing import Coroutine, Dict, Iterable, List, Optional

from ..cfg import EVENT_BLACKLIST
from ..protocols import Event, OnHandler, Subscriptions
from ..utils import wildcard_search
from .aeventbus import AEventBus

logger = logging.getLogger(__name__)


class EventBus(AEventBus):
    def __init__(self):
        super().__init__()
        self._running = True
        self._wildcard_subs: Dict[str, Dict[str, Subscriptions]] = defaultdict(dict)

    async def _on(self, id: str, handler: OnHandler):
        sub = Subscriptions(id, handler)
        if "*" in handler.event_type:
            self._wildcard_subs[handler.event_type][id] = sub
        else:
            self._subs[handler.event_type][id] = sub

    def _remove(self, id: str):
        for route, subs in self._subs.items():
            if id in subs:
                del self._subs[route][id]

    async def _exec(
        self, coros: List[Coroutine], event: Event, subs: Iterable[Subscriptions]
    ):

        for sub in subs:
            # If async function, await it
            if asyncio.iscoroutinefunction(sub.handler.handler):
                coros.append(sub.handler.handler(event))
            else:
                sub.handler.handler(event)

    async def _emit(self, event: Event):

        coros: List[Coroutine] = []

        # Handle wildcard subscriptions
        for match in wildcard_search(event.type, self._wildcard_subs.keys()):
            await self._exec(coros, event, self._wildcard_subs[match].values())

        # Else, normal subscriptions
        await self._exec(coros, event, self._subs[event.type].values())

        # Wait for all async functions to finish
        if len(coros) > 0:
            await asyncio.gather(*coros)

    ####################################################################
    ## Front-Facing API
    ####################################################################

    async def forward(
        self, ip: str, port: int, event_types: Optional[List[str]] = None
    ):
        from ..entrypoint import DEntryPoint

        # Handle default event types
        if event_types is None:
            event_types = ["*"]

        # Create entrypoint
        e = DEntryPoint()
        await e.connect(ip, port)
        for event_type in event_types:

            async def _wrapper(event: Event):
                await e.emit(event.type, event.data, event.id)

            handler = OnHandler(event_type, _wrapper)
            await self._on(f"{ip}:{port}", handler)

    async def deforward(self, ip: str, port: int):
        self._remove(f"{ip}:{port}")

    async def close(self):
        # Emit first to allow for cleanup
        await self._emit(Event("aiodistbus.eventbus.close"))
        self._running = False
