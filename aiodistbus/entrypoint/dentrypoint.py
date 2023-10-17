import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional, Type

import asyncio_atexit
import zmq
import zmq.asyncio

from ..messages import Message, SubscribeData
from ..protocols import Event, OnHandler
from .aentrypoint import AEntryPoint

logger = logging.getLogger("aiodistbus")


class DEntryPoint(AEntryPoint):
    def __init__(self):
        super().__init__()

        # Parameters
        self._running: bool = False
        self.run_task: Optional[asyncio.Task] = None
        self.snapshot: Optional[zmq.asyncio.Socket] = None
        self.subscriber: Optional[zmq.asyncio.Socket] = None
        self.publisher: Optional[zmq.asyncio.Socket] = None

        asyncio_atexit.register(self.close)

    async def _run(self):
        assert self.subscriber, "SUB socket not initialized"

        # After connect and identify established, listen
        while self._running:
            event_list = await self.poller.poll(timeout=1000)
            events = dict(event_list)

            # Empty if no events
            if len(events) == 0:
                continue

            for s in events:
                data = await s.recv()
                logger.debug(data)

    async def _update_handlers(self, event_type: Optional[str] = None):
        if not self.snapshot:
            return

        if event_type:
            msg = Message("SUBSCRIBE", SubscribeData(event_type=[event_type]))
            await self.snapshot.send(msg.to_json().encode())
        else:
            msg = Message(
                "SUBSCRIBE", SubscribeData(event_type=list(self._handlers.keys()))
            )
            await self.snapshot.send(msg.to_json().encode())

    ####################################################################
    ## Front-Facing API
    ####################################################################

    async def on(self, event_type: str, handler: Callable, dataclass: Type):
        wrapped_handler = self._wrapper(handler)
        on_handler = OnHandler(event_type, wrapped_handler, dataclass)
        self._handlers[event_type] = on_handler
        await self._update_handlers(event_type)

    async def emit(self, event_type: str, data: Any) -> Optional[Event]:
        if not self.snapshot or not self.publisher:
            logger.warning("Not connected to server")
            return None

        msg = Message("EVENT", Event(event_type, data))
        await self.publisher.send(msg.to_json().encode())
        event = Event(event_type, data)
        return event

    async def connect(self, ip: str, port: int):

        self.ctx = zmq.asyncio.Context()
        self.snapshot = self.ctx.socket(zmq.DEALER)
        self.snapshot.setsockopt(zmq.IDENTITY, self.id.encode("utf-8"))
        self.snapshot.connect(f"tcp://{ip}:{port}")
        self.subscriber = self.ctx.socket(zmq.SUB)
        self.subscriber.connect(f"tcp://{ip}:{port+1}")
        self.publisher = self.ctx.socket(zmq.PUSH)
        self.publisher.connect(f"tcp://{ip}:{port+2}")
        await asyncio.sleep(0.3)

        # Keeping track of state
        self._running = True

        # First, use snapshot to connect
        await self.snapshot.send(Message("CONNECT", {}).to_json().encode())

        # Then, inform server the type of events we want to listen to
        await self._update_handlers()

        # Using a poller for the subscriber
        self.poller = zmq.asyncio.Poller()
        self.poller.register(self.subscriber, zmq.POLLIN)
        self.run_task = asyncio.create_task(self._run())

    async def close(self):

        if self._running:
            self._running = False
            if self.run_task:
                await self.run_task
            if self.snapshot:
                await self.snapshot.send(Message("DISCONNECT", {}).to_json().encode())
                self.snapshot.close()
            if self.subscriber:
                self.subscriber.close()
            if self.publisher:
                self.publisher.close()

            self.ctx.term()
