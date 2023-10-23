import asyncio
import logging

import asyncio_atexit
import zmq
import zmq.asyncio

from ..protocols import Event, OnHandler, Subscriptions
from ..utils import get_ip_address
from .aeventbus import AEventBus

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
        await self._emit(topic, msg)

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

    async def close(self):
        
        if self._running:
            await self._emit(b"eventbus.close", Event("eventbus.close").to_json().encode())
            self._running = False
            await self.run_task

            # Close sockets
            self.snapshot.close()
            self.publisher.close()
            self.collector.close()
            self.ctx.term()
