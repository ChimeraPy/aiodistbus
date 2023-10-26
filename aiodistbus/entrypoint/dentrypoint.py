import asyncio
import logging
from typing import Any, Callable, Coroutine, List, Optional, Type, Union

import asyncio_atexit
import zmq
import zmq.asyncio

from ..protocols import Event, Handler
from ..timer import Timer
from ..utils import encode, reconstruct, wildcard_filtering
from .aentrypoint import AEntryPoint

logger = logging.getLogger("aiodistbus")


class DEntryPoint(AEntryPoint):
    def __init__(self, pulse_ttl: Union[int, float] = 50, pulse_limit: int = 4):
        super().__init__()

        # Pulse
        self.pulse_ttl = pulse_ttl
        self.pulse_timer: Optional[Timer] = None
        self.pulse_count: int = 0
        self.pulse_fail: int = 0
        self.pulse_limit: int = pulse_limit
        self._on_disrupt: Optional[Callable] = None

        # Primary ZeroMQ Client
        self._running: bool = False
        self._lock: asyncio.Lock = asyncio.Lock()
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
                # logger.debug(f"SUBSCRIBER: Received {topic} - {event}")

                # Reconstruct the data
                if topic in self._handlers:
                    known_type = self._handlers[topic].dtype
                else:
                    known_type = None
                event = await reconstruct(event, known_type)

                # Obtain the handlers
                coros: List[Coroutine] = []
                if topic in self._handlers:
                    coros.append(self._handlers[topic].function(event))
                for handler in self._wildcards.values():
                    if wildcard_filtering(topic, handler.event_type):
                        coros.append(handler.function(event))

                # Await the handlers
                if len(coros) > 0:
                    await asyncio.gather(*coros)

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

    async def _pulse_sub(self):
        self.pulse_count += 1

    async def _pulse_check(self):

        # Check if there is a pulse
        if self.pulse_count == 0:
            self.pulse_fail += 1
        else:
            self.pulse_fail = 0

        # If too many failures, close
        if self.pulse_fail > self.pulse_limit:
            logger.error(f"aiodistbus: Pulse failure limit reached")
            if self._on_disrupt:
                await self._on_disrupt()
            await self.close()
            return

        # Reset pulse count
        self.pulse_count = 0

    ####################################################################
    ## Front-Facing API
    ####################################################################

    @property
    def running(self) -> bool:
        return self._running

    async def emit(
        self, event_type: str, data: Any, id: Optional[str] = None
    ) -> Optional[Event]:
        if not self.snapshot or not self.publisher:
            logger.warning("Not connected to server")
            return None

        # Encode data
        data = encode(data)

        # Package data with an Event object
        if id:
            event = Event(event_type, data, id=id)
        else:
            event = Event(event_type, data)

        # Send the data
        # logger.debug(f"PUBLISHER: {event}")
        try:
            await self.publisher.send_multipart(
                [event_type.encode("utf-8"), event.to_json().encode()]
            )
        except zmq.error.ZMQError:
            logger.error("Could not send event")
            return None
        return event

    async def connect(self, ip: str, port: int, on_disrupt: Optional[Callable] = None):

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
        await self.on("aiodistbus.eventbus.close", self.close, create_task=True)
        await self.on("aiodistbus.eventbus.pulse", self._pulse_sub)
        await self._update_handlers()

        # First, use snapshot to connect
        await self.snapshot.send("CONNECT".encode())

        # Using a poller for the subscriber
        self.poller = zmq.asyncio.Poller()
        self.poller.register(self.subscriber, zmq.POLLIN)
        self.run_task = asyncio.create_task(self._run())

        # Create task check the pulse
        if on_disrupt:
            self._on_disrupt = on_disrupt
        self.pulse_timer = Timer(self._pulse_check, self.pulse_ttl)
        self.pulse_timer.start()

    async def close(self):

        # If not closed already, close
        async with self._lock:
            if self._running:

                # Stop the main task
                self._running = False
                if self.run_task:
                    await self.run_task

                # Stop the timer
                if self.pulse_timer:
                    await self.pulse_timer.stop()

                if not self.ctx.closed:
                    if self.snapshot:
                        await self.snapshot.send("DISCONNECT".encode())
                        self.snapshot.close()
                    if self.subscriber:
                        self.subscriber.close()
                    if self.publisher:
                        self.publisher.close()
