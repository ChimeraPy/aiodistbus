import asyncio
import logging
import typing
from collections import defaultdict
from typing import Coroutine, Dict, Iterable, List, Optional, Type, Union

from ..protocols import Event, Handler, Subscriptions
from ..utils import wildcard_search
from .aeventbus import AEventBus

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from ..entrypoint import DEntryPoint


class EventBus(AEventBus):
    """Eventbus

    This class is the eventbus. It handles all subscriptions and emits events to
    the appropriate handlers.

    """

    def __init__(self):
        super().__init__()
        self._running = True
        self._wildcard_subs: Dict[str, Dict[str, Subscriptions]] = defaultdict(dict)
        self._dtypes: Dict[str, Union[Type, None]] = {}
        self._dentrypoints: Dict[str, DEntryPoint] = {}

    async def _on(self, id: str, handler: Handler):
        sub = Subscriptions(id, handler)
        if "*" in handler.event_type:
            self._wildcard_subs[handler.event_type][id] = sub
        else:
            self._subs[handler.event_type][id] = sub
            self._dtypes[handler.event_type] = handler.dtype

    async def _off(self, id: str, event_type: str):
        if "*" in event_type:
            del self._wildcard_subs[event_type][id]
        else:
            del self._subs[event_type][id]
            del self._dtypes[event_type]

    def _remove(self, id: str):
        to_be_removed: List[str] = []
        for route, subs in self._subs.items():
            if id in subs:
                del self._subs[route][id]
                if len(self._subs[route]) == 0:
                    to_be_removed.append(route)

        for route in to_be_removed:
            del self._subs[route]
            del self._dtypes[route]

    async def _exec(
        self, coros: List[Coroutine], event: Event, subs: Iterable[Subscriptions]
    ):

        for sub in subs:
            # If async function, await it
            if asyncio.iscoroutinefunction(sub.handler.function):
                coros.append(sub.handler.function(event))
            else:
                sub.handler.function(event)

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
        """Forward events to another eventbus

        Args:
            ip (str): IP address of the eventbus
            port (int): Port of the eventbus
            event_types (Optional[List[str]], optional): Event types to forward. Defaults to None.

        Examples:
            >>> bus = EventBus()
            >>> dbus = DEventBus()
            >>> await bus.forward(dbus.ip, dbus.port, ["hello"])

        """
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

            handler = Handler(event_type, _wrapper)
            await self._on(f"{ip}:{port}", handler)

        # Store the entrypoint
        self._dentrypoints[f"{ip}:{port}"] = e

    async def deforward(self, ip: str, port: int):
        """Remove forwarding to another eventbus

        Args:
            ip (str): IP address of the eventbus
            port (int): Port of the eventbus

        """
        # Remove handlers
        self._remove(f"{ip}:{port}")

        # Remove entrypoint
        await self._dentrypoints[f"{ip}:{port}"].close()
        del self._dentrypoints[f"{ip}:{port}"]

    async def close(self):
        """Close the eventbus"""
        # Emit first to allow for cleanup
        await self._emit(Event("aiodistbus.eventbus.close"))
        self._running = False

        # Close all entrypoints
        for e in self._dentrypoints.values():
            await e.close()
