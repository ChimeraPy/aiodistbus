import asyncio
import logging

import zmq
import zmq.asyncio

from ..protocols import Event, OnHandler, Subscriptions
from ..utils import get_ip_address
from .aeventbus import AEventBus

logger = logging.getLogger(__name__)


class DEventBus:
    def __init__(self, port: int):
        super().__init__()

        # Parameters
        self._ip: str = get_ip_address()
        self._port: int = port
        self._running: bool = False

        # Set up clone server sockets
        self.ctx = zmq.asyncio.Context()
        self.snapshot = self.ctx.socket(zmq.ROUTER)
        self.publisher = self.ctx.socket(zmq.PUB)
        self.collector = self.ctx.socket(zmq.PULL)
        self.snapshot.bind("tcp://*:%d" % self.port)
        self.publisher.bind("tcp://*:%d" % (self.port + 1))
        self.collector.bind("tcp://*:%d" % (self.port + 2))

        # Create poller to listen to snapshot and collector
        self.poller = zmq.asyncio.Poller()
        self.poller.register(self.snapshot, zmq.POLLIN)
        self.poller.register(self.collector, zmq.POLLIN)

        self._running = True
        self.run_task = asyncio.create_task(self._run())

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port

    # async def _snapshot_reactor(self):
    #     while self._running:
    #         [id, msg] = await self.snapshot.recv_multipart()
    #         logger.debug(f"Received {id} {msg}")

    # async def _collector_reactor(self):
    #     while self._running:
    #         [topic, msg] = await self.collector.recv_multipart()
    #         logger.debug(f"Received {topic} {msg}")

    async def _run(self):
        while self._running:

            event_list = await self.poller.poll(timeout=10)
            events = dict(event_list)

            # Empty if no events
            if len(events) == 0:
                continue

            if self.snapshot in events:
                [id, msg] = await self.snapshot.recv_multipart()
                logger.debug(f"Received {id} {msg}")

            if self.collector in events:
                [topic, msg] = await self.collector.recv_multipart()
                logger.debug(f"Received {topic} {msg}")

    ####################################################################
    ## Front-Facing API
    ####################################################################

    async def close(self):

        if self._running:
            self._running = False
            await self.run_task

        self.snapshot.close()
        self.publisher.close()
        self.collector.close()
        self.ctx.term()
