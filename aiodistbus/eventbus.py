import abc
from dataclasses import dataclass
from typing import Dict, List, Literal, Type

import zmq

from .protocols import Event, OnHandler
from .utils import get_ip_address

@dataclass
class Subscription:
    entrypoint: str
    event_type: str
    dataclass: Type["T"]


class AEventBus(abc.ABC):
    
    def __init__(self):

        # State information
        self._routes: Dict[str, List[Subscription]] = {}

    @abc.abstractmethod
    async def aserve(self):
        ...
    
    @abc.abstractmethod
    async def extend(self, event_type: str):
        ...

    @abc.abstractmethod
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

        # Register our handlers with reactor
        self.snapshot.on_recv(self.handle_snapshot)
        self.collector.on_recv(self.handle_collect)
        self.flush_callback = PeriodicCallback(self.flush_ttl, 1000)
    
    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port


class EventBus():
    ...
