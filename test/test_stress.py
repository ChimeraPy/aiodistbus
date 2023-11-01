import asyncio
import logging
import uuid
from dataclasses import dataclass
from typing import List

import pytest
from dataclasses_json import DataClassJsonMixin

from aiodistbus import DEntryPoint, DEventBus

logger = logging.getLogger("aiodistbus")

N = 5
M = 100


@dataclass
class StressTestEvent(DataClassJsonMixin):
    extra_id: str


@pytest.mark.repeat(N)
async def test_create_dbus():
    bus = DEventBus("127.0.0.1")
    await asyncio.wait_for(bus.close(), timeout=3)


@pytest.mark.repeat(N)
async def test_dbus_entrypoint():
    bus = DEventBus("127.0.0.1")
    e = DEntryPoint()
    await e.connect(bus.ip, bus.port)
    await asyncio.wait_for(bus.close(), timeout=3)
    await asyncio.wait_for(e.close(), timeout=3)


@pytest.mark.repeat(N)
async def test_entrypoint_dbus():
    bus = DEventBus("127.0.0.1")
    e = DEntryPoint()
    await e.connect(bus.ip, bus.port)
    await asyncio.wait_for(e.close(), timeout=3)
    await asyncio.wait_for(bus.close(), timeout=3)


async def test_bus_emit_stress(bus, entrypoints):
    # Create resources
    e1, e2 = entrypoints
    container: List[str] = []

    async def func(event: StressTestEvent):
        nonlocal container
        assert isinstance(event, StressTestEvent)
        container.append(event.extra_id)

    # Add funcs
    await e1.on("test", func, StressTestEvent)

    # Connect
    await e1.connect(bus)
    await e2.connect(bus)

    # Send message
    events: List = []
    for _ in range(M):
        instance = StressTestEvent(str(uuid.uuid4()))
        event = await e2.emit("test", instance)
        events.append(event)

    # Assert
    fails: List = []
    for event in events:
        if event.data.extra_id not in container:
            fails.append(event.data.extra_id)

    logger.debug(f"fails: {len(fails)/M}")
    assert len(fails) == 0


async def test_dbus_emit_stress(dbus, dentrypoints):
    # Create resources
    e1, e2 = dentrypoints
    container: List[str] = []

    async def func(event: StressTestEvent):
        nonlocal container
        assert isinstance(event, StressTestEvent)
        container.append(event.extra_id)

    # Add funcs
    await e1.on("test", func, StressTestEvent)

    # Connect
    await e1.connect(dbus.ip, dbus.port)
    await e2.connect(dbus.ip, dbus.port)

    # Send message
    events: List = []
    for _ in range(M):
        instance = StressTestEvent(str(uuid.uuid4()))
        event = await e2.emit("test", instance)
        events.append(event)

    # Need to flush
    await dbus.flush()

    # Assert
    fails: List = []
    for event in events:
        if StressTestEvent.from_json(event.data.decode()).extra_id not in container:
            fails.append(event.data.extra_id)

    logger.debug(f"fails: {len(fails)/M}")
    assert len(fails) == 0
