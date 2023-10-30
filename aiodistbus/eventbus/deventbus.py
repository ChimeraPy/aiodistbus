import asyncio
import logging
import zlib
from collections import defaultdict
from typing import Dict, List, Optional, Type, Union

import asyncio_atexit
import zmq
import zmq.asyncio

from ..cfg import EVENT_BLACKLIST
from ..protocols import Event
from ..timer import Timer
from ..utils import reconstruct, verify_checksum, wildcard_search
from .aeventbus import AEventBus
from .eventbus import EventBus

logger = logging.getLogger("aiodistbus")


class DEventBus(AEventBus):
    """Distributed eventbus

    This class is the distributed eventbus. This is the server in that
    broadcasts events to all clients. It also handles the local eventbuses
    and forwards events to them.

    """

    def __init__(
        self, ip: str = "127.0.0.1", port: int = 0, pulse: Union[float, int] = 15
    ):
        """Initialize the distributed eventbus

        Args:
            ip (str): IP address to bind to. Defaults to '127.0.0.1'
            port (int, optional): Port to bind to. Defaults to 0.
            pulse (Union[float, int], optional): Pulse interval. Defaults to 15.

        """
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

        if port == 0:
            port = self.snapshot.bind_to_random_port(f"tcp://{ip}")
            self.publisher.bind(f"tcp://{ip}:{port+1}")
            self.collector.bind(f"tcp://{ip}:{port+2}")
            self._port = port
        else:
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

        # Create a timer to pulse to all clients
        # Letting them know if the server is alive
        self.timer = Timer(self._pulse, pulse)
        self.timer.start()

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

    async def _emit(self, topic: bytes, msg: bytes, checksum: Optional[bytes] = None):
        if checksum is None:
            checksum = zlib.crc32(msg).to_bytes(4, "big")
        await self.publisher.send_multipart([topic, msg, checksum])

    async def _snapshot_reactor(self, id: bytes, msg: bytes):
        # logger.debug(f"ROUTER: Received {id}: {msg}")

        # Decode message
        dmsg = msg.decode()
        if dmsg == "aiodistbus.eventbus.connect":
            await self.snapshot.send_multipart([id, b"aiodistbus.eventbus.handshake"])

    async def _collector_reactor(self, topic: bytes, msg: bytes, checksum: bytes):

        # Broadcast via socket
        await self._emit(topic, msg, checksum)

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
                await self._snapshot_reactor(id, msg)

            if self.collector in events:
                [topic, data, checksum] = await self.collector.recv_multipart()

                # Check if the checksum is correct
                if verify_checksum(data, checksum):
                    await self._collector_reactor(topic, data, checksum)
                else:
                    logger.error("aiodistbus: Checksum failed for %s", topic.decode())

    async def _pulse(self):
        event_d = Event("aiodistbus.eventbus.pulse").to_json().encode()
        await self._emit(b"aiodistbus.eventbus.pulse", event_d)

    ####################################################################
    ## Front-Facing API
    ####################################################################

    async def flush(self):
        """Flush the eventbus"""
        self._flush_flag.clear()
        await self._flush_flag.wait()

    async def forward(self, bus: EventBus, event_types: Optional[List[str]] = None):
        """Forward events to a local eventbus

        Args:
            bus (EventBus): Local eventbus
            event_types (Optional[List[str]], optional): Event types to forward. Defaults to None.

        Exapmles:
            >>> bus = EventBus()
            >>> dbus = DEventBus()
            >>> await dbus.forward(bus, ["hello"])

        """
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
        """Close the eventbus"""

        if self._running:

            # Inform to stop
            event_d = Event("aiodistbus.eventbus.close").to_json().encode()
            await self._emit(b"aiodistbus.eventbus.close", event_d)

            # Stop the main routine
            self._running = False
            await self.run_task

            # Stop the pulse
            await self.timer.stop()

            # Close sockets
            self.snapshot.close()
            self.publisher.close()
            self.collector.close()
            self.ctx.term()
