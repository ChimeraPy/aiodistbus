import asyncio
import logging
from typing import Coroutine, Dict, Iterable, List

from ..protocols import Event, OnHandler, Subscriptions
from .aeventbus import AEventBus

logger = logging.getLogger(__name__)


class EventBus(AEventBus):
    def __init__(self):
        super().__init__()
        self._running = True
        self._wildcard_subs: Dict[str, Dict[str, Subscriptions]] = {}

    async def _on(self, id: str, handler: OnHandler):
        sub = Subscriptions(id, handler)
        if "*" in handler.event_type:
            if handler.event_type not in self._wildcard_subs:
                self._wildcard_subs[handler.event_type] = {}
            self._wildcard_subs[handler.event_type][id] = sub
        else:
            if handler.event_type not in self._subs:
                self._subs[handler.event_type] = {}
            self._subs[handler.event_type][id] = sub

    def _remove(self, id: str):
        for route, subs in self._subs.items():
            if id in subs:
                del self._subs[route][id]

    async def _exec(self, event: Event, subs: Iterable[Subscriptions]):
        coros: List[Coroutine] = []
        for sub in subs:
            # If async function, await it
            if asyncio.iscoroutinefunction(sub.handler.handler):
                coros.append(sub.handler.handler(event))
            else:
                sub.handler.handler(event)

        # Wait for all async functions to finish
        if len(coros) > 0:
            await asyncio.gather(*coros)

    async def _emit(self, event: Event):
        # import pdb; pdb.set_trace()

        # Handle wildcard subscriptions
        for wildcard, subs in self._wildcard_subs.items():
            for i, j in zip(event.type.split("."), wildcard.split(".")):
                if j == "*":
                    await self._exec(event, subs.values())
                    break
                elif i != j:
                    break

        # Else, normal subscriptions
        if event.type not in self._subs:
            return
        else:
            await self._exec(event, self._subs[event.type].values())

    ####################################################################
    ## Front-Facing API
    ####################################################################

    async def close(self):
        self._running = False
