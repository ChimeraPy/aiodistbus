from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Literal, Type

import zmq
import zmq.asyncio

from .protocols import Event, OnHandler
from .utils import get_ip_address

@dataclass
class Subscription:
    entrypoint: str
    event_type: str
    dataclass: Type


class AEventBus(ABC):
    
    def __init__(self):

        # State information
        self._running = False
        self._subscriptions: Dict[str, List[Subscription]] = {}

    @property
    def running(self):
        return self._running

    @abstractmethod
    async def emit(self, event: Event):
        ...

    @abstractmethod
    async def extend(self, event_type: str):
        ...

    # @abstractmethod
    async def close(self):
        ...


class DEventBus():

    def __init__(self, port: int):

        # Parameters
        self.ctx = zmq.asyncio.Context()
        self._ip: str = get_ip_address()
        self._port: int = port

        # Set up clone server sockets
        self.snapshot  = self.ctx.socket(zmq.ROUTER)
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


class EventBus():

    def __init__(self):
        super().__init__()
        self._running = True

    async def emit(self):
        # Get subscriptions based on event type
        ...
    
    async def close(self):
        ...
