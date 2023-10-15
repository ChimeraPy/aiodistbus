import asyncio
from typing import (
    Any,
    Callable,
    Optional,
    Type,
)

import zmq
import zmq.asyncio

from ..protocols import Event, OnHandler
from .aentrypoint import AEntryPoint


class DEntryPoint(AEntryPoint):
    def __init__(self):
        super().__init__()

        # Parameters
        self._running: bool = False
        self.run_task: Optional[asyncio.Task] = None
        self.snapshot: Optional[zmq.asyncio.Socket] = None
        self.subscriber: Optional[zmq.asyncio.Socket] = None
        self.publisher: Optional[zmq.asyncio.Socket] = None

    async def _run(self):
        await asyncio.gather(
            self._subscriber_reactor(),
        )

    async def _subscriber_reactor(self):
        assert self.subscriber, "Subscriber socket not initialized"
        while self._running:
            [topic, msg] = await self.subscriber.recv()

    async def _update_handlers(self):
        ...

    ####################################################################
    ## Front-Facing API
    ####################################################################

    async def on(self, event_type: str, handler: Callable, dataclass: Type):
        wrapped_handler = self._wrapper(handler)
        on_handler = OnHandler(event_type, wrapped_handler, dataclass)
        self._handlers[event_type] = on_handler
        await self._update_handlers()

    async def emit(self, event_type: str, data: Any) -> Event:
        event = Event(event_type, data)
        return event

    async def connect(self, ip: str, port: int):

        self._running = True
        self.ctx = zmq.asyncio.Context()
        self.snapshot = self.ctx.socket(zmq.DEALER)
        self.snapshot.connect("tcp://%s:%d" % (ip, port))
        self.subscriber = self.ctx.socket(zmq.SUB)
        self.subscriber.connect("tcp://%s:%d" % (ip, port + 1))
        self.publisher = self.ctx.socket(zmq.PUSH)
        self.publisher.connect("tcp://%s:%d" % (ip, port + 2))

        self.run_task = asyncio.create_task(self._run())

    async def close(self):

        if self._running:
            self._running = False
            if self.run_task:
                await self.run_task
            if self.snapshot:
                self.snapshot.close()
            if self.subscriber:
                self.subscriber.close()
            if self.publisher:
                self.publisher.close()

        self.ctx.term()
