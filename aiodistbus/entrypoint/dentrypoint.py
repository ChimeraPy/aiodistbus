import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional, Type

import asyncio_atexit
import zmq
import zmq.asyncio
from dataclasses_json import DataClassJsonMixin

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
                [topic, event] = await s.recv_multipart()
                topic = topic.decode("utf-8")
                event = event.decode("utf-8")

                # With the data, use the handler
                if topic in self._handlers:

                    # Reconstruct the data
                    dtype = self._handlers[topic].dtype
                    event = Event.from_json(event)
                    if dtype:
                        event.data = dtype(**event.data)

                    # Pass through the handler
                    handler = self._handlers[topic].handler
                    await handler(event)

                # Check for wildcards
                for wildcard in self._wildcards:
                    for i, j in zip(topic.split("."), wildcard.split(".")):
                        if j == "*":

                            # Reconstruct the data (if needed)
                            if not isinstance(event, Event):
                                event = Event.from_json(event)

                            # Pass through the handler
                            handler = self._wildcards[wildcard].handler
                            await handler(event)
                            break
                        if i != j:
                            break

    async def _update_handlers(self, event_type: Optional[str] = None):
        if not self.subscriber:
            return

        if event_type:
            self.subscriber.setsockopt(zmq.SUBSCRIBE, event_type.encode("utf-8"))
            # logger.debug("SUBSCRIBER: Subscribed to %s", event_type)
        else:
            for event_type in self._handlers.keys():
                self.subscriber.setsockopt(zmq.SUBSCRIBE, event_type.encode("utf-8"))
                # logger.debug("SUBSCRIBER: Subscribed to %s", event_type)

    ####################################################################
    ## Front-Facing API
    ####################################################################

    async def on(
        self, event_type: str, handler: Callable, dtype: Optional[Type] = None
    ):

        # Track handlers (supporting wildcards)
        if "*" not in event_type:
            wrapped_handler = self._wrapper(handler)
            on_handler = OnHandler(event_type, wrapped_handler, dtype)
            self._handlers[event_type] = on_handler
        else:
            wrapped_handler = self._wrapper(handler, unpack=False)
            on_handler = OnHandler(event_type, wrapped_handler, dtype)
            self._wildcards[event_type] = on_handler

        await self._update_handlers(event_type)

    async def emit(self, event_type: str, data: DataClassJsonMixin) -> Optional[Event]:
        if not self.snapshot or not self.publisher:
            logger.warning("Not connected to server")
            return None

        event = Event(event_type, data)
        await self.publisher.send_multipart(
            [event_type.encode("utf-8"), event.to_json().encode()]
        )
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

        # Update the subscriber's topics
        await self._update_handlers()

        # First, use snapshot to connect
        await self.snapshot.send("CONNECT".encode())

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
                await self.snapshot.send("DISCONNECT".encode())
                self.snapshot.close()
            if self.subscriber:
                self.subscriber.close()
            if self.publisher:
                self.publisher.close()

            self.ctx.term()
