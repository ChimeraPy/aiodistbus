import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Coroutine, Dict, List, Type, Union

import zmq
import zmq.asyncio

from .protocols import Event, OnHandler, Subscriptions
from .utils import get_ip_address


class AEventBus(ABC):
    def __init__(self):

        # State information
        self._running = False
        self._subs: Dict[str, Dict[str, Subscriptions]] = {}

    @property
    def running(self):
        return self._running

    @abstractmethod
    async def on(self, event_type: str, dataclass: Type):
        ...

    @abstractmethod
    async def emit(self, event: Event):
        ...

    # @abstractmethod
    async def extend(self, event_type: str):
        ...

    # @abstractmethod
    async def close(self):
        ...


class DEventBus:
    def __init__(self, port: int):

        # Parameters
        self.ctx = zmq.asyncio.Context()
        self._ip: str = get_ip_address()
        self._port: int = port

        # Set up clone server sockets
        self.snapshot = self.ctx.socket(zmq.ROUTER)
        self.publisher = self.ctx.socket(zmq.PUB)
        self.collector = self.ctx.socket(zmq.PULL)
        self.snapshot.bind("tcp://*:%d" % self.port)
        self.publisher.bind("tcp://*:%d" % (self.port + 1))
        self.collector.bind("tcp://*:%d" % (self.port + 2))

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port


class EventBus(AEventBus):
    def __init__(self):
        super().__init__()
        self._running = True

    async def on(self, id: str, handler: OnHandler):
        sub = Subscriptions(id, handler)
        if handler.event_type not in self._subs:
            self._subs[handler.event_type] = {}
        self._subs[handler.event_type][id] = sub

    async def emit(self, event: Event):
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

    async def close(self):
        ...
