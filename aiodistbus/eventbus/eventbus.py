import asyncio
import logging
from typing import Coroutine, List

from ..protocols import Event, OnHandler, Subscriptions
from .aeventbus import AEventBus

logger = logging.getLogger(__name__)


class EventBus(AEventBus):
    def __init__(self):
        super().__init__()
        self._running = True

    async def _on(self, id: str, handler: OnHandler):
        sub = Subscriptions(id, handler)
        if handler.event_type not in self._subs:
            self._subs[handler.event_type] = {}
        self._subs[handler.event_type][id] = sub

    def _remove(self, id: str):
        for route, subs in self._subs.items():
            if id in subs:
                del self._subs[route][id]

    async def _emit(self, event: Event):
        if event.type not in self._subs:
            return

        coros: List[Coroutine] = []
        for sub in self._subs[event.type].values():
            # If async function, await it
            if asyncio.iscoroutinefunction(sub.handler.handler):
                coros.append(sub.handler.handler(event))
            else:
                sub.handler.handler(event)

        # Wait for all async functions to finish
        if len(coros) > 0:
            await asyncio.gather(*coros)

    ####################################################################
    ## Front-Facing API
    ####################################################################

    async def close(self):
        self._running = False
