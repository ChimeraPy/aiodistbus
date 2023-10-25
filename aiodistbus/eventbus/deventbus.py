import asyncio
import logging
from collections import defaultdict
from typing import Dict, List, Optional, Type

import asyncio_atexit
import zmq
import zmq.asyncio

from ..cfg import EVENT_BLACKLIST
from ..protocols import Event
from ..utils import reconstruct, wildcard_search
from .eventbus import EventBus

logger = logging.getLogger("aiodistbus")


class DEventBus:
    def __init__(self, ip: str, port: int):
        super().__init__()

        # Parameters
        self._ip: str = ip
        self._port: int = port
        self._running: bool = False

        # Set up clone server sockets
        self.ctx = zmq.asyncio.Context()
        self.snapshot = self.ctx.socket(zmq.ROUTER)
        self.publisher = self.ctx.socket(zmq.PUB)
        self.collector = self.ctx.socket(zmq.PULL)
        self.snapshot.bind(f"tcp://{ip}:{port}")
        self.publisher.bind(f"tcp://{ip}:{port+1}")
        self.collector.bind(f"tcp://{ip}:{port+2}")

        # Create poller to listen to snapshot and collector
        self.poller = zmq.asyncio.Poller()
        self.poller.register(self.snapshot, zmq.POLLIN)
        self.poller.register(self.collector, zmq.POLLIN)

        self._running = True
        self._flush_flag = asyncio.Event()
        self._flush_flag.clear()
        self.run_task = asyncio.create_task(self._run())

        asyncio_atexit.register(self.close)

        # Local event buses
        self._lbuses_wildcard: Dict[str, List[EventBus]] = defaultdict(list)
        self._lbuses_subs: Dict[str, List[EventBus]] = defaultdict(list)

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port

    async def _emit(self, topic: bytes, msg: bytes):
        await self.publisher.send_multipart([topic, msg])

    async def _snapshot_reactor(self, id: str, msg: bytes):
        ...
        # logger.debug(f"ROUTER: Received {id}: {msg}")

    async def _collector_reactor(self, topic: bytes, msg: bytes):

        # Broadcast via socket
        await self._emit(topic, msg)

        # Only perform this if we have local buses
        if len(self._lbuses_wildcard) == 0 and len(self._lbuses_subs) == 0:
            return

        # If local buses, send them the data
        dtopic = topic.decode()

        # Handle wildcard subscriptions
        bus_to_emit: List[EventBus] = []
        if dtopic not in EVENT_BLACKLIST:
            for match in wildcard_search(dtopic, self._lbuses_wildcard.keys()):
                for bus in self._lbuses_wildcard[match]:
                    # logger.debug(f"{dtopic}: {msg}")
                    bus_to_emit.append(bus)

        # Else, normal subscriptions
        if dtopic in self._lbuses_subs:
            for bus in self._lbuses_subs[dtopic]:
                # logger.debug(f"{dtopic}: {msg}")
                bus_to_emit.append(bus)

        # Identify if any bus has the dtype
        known_type: Optional[Type] = None
        for bus in bus_to_emit:
            if dtopic in bus._dtypes:
                known_type = bus._dtypes[dtopic]

        # Reconstruct the data
        event = await reconstruct(msg.decode(), known_type)

        # Emit the event
        for bus in bus_to_emit:
            await bus._emit(event)

    async def _run(self):
        while self._running:

            event_list = await self.poller.poll(timeout=1000)
            events = dict(event_list)

            # Empty if no events
            if len(events) == 0:
                self._flush_flag.set()
                continue

            if self.snapshot in events:
                [id, msg] = await self.snapshot.recv_multipart()
                await self._snapshot_reactor(id.decode(), msg)

            if self.collector in events:
                [topic, data] = await self.collector.recv_multipart()
                await self._collector_reactor(topic, data)

    ####################################################################
    ## Front-Facing API
    ####################################################################

    async def flush(self):
        self._flush_flag.clear()
        await self._flush_flag.wait()

    async def forward(self, bus: EventBus, event_types: Optional[List[str]] = None):

        # Handle default event types
        if event_types is None:
            event_types = ["*"]

        # Link
        for event_type in event_types:
            if "*" in event_type:
                self._lbuses_wildcard[event_type].append(bus)
            else:
                self._lbuses_subs[event_type].append(bus)

    async def close(self):

        if self._running:
            event_d = Event("aiodistbus.eventbus.close").to_json().encode()
            await self._emit(b"aiodistbus.eventbus.close", event_d)
            self._running = False
            await self.run_task

            # Close sockets
            self.snapshot.close()
            self.publisher.close()
            self.collector.close()
            self.ctx.term()
