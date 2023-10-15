import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List

import pytest
from dataclasses_json import DataClassJsonMixin

from aiodistbus import EntryPoint, EventBus

logger = logging.getLogger(__name__)


@dataclass
class ExampleEvent:
    msg: str


async def handler(event: ExampleEvent):
    logger.info(f"Received event {event}")


@pytest.fixture
async def bus():
    bus = EventBus()
    yield bus
    await bus.close()


async def test_local_eventbus(bus):

    # Create resources
    entry1 = EntryPoint()
    entry2 = EntryPoint()

    # Add handlers
    await entry1.on("test", handler, ExampleEvent)
    await entry1.on("hello", handler, ExampleEvent)
    await entry1.on("test/hello", handler, ExampleEvent)

    # Connect
    await entry1.connect(bus)
    await entry2.connect(bus)

    # Send message
    event = await entry2.emit("test", ExampleEvent("Hello"))

    # Assert
    assert event.id in entry1._received
    assert len(entry1._received) == 1
    await entry1.close()
    await entry2.close()


async def test_remote_eventbus(bus):

    # Create resources
    entry1 = EntryPoint("entry1")
    entry2 = EntryPoint("entry2")

    # Add handlers
    await entry1.on("test", handler, ExampleEvent)

    # Connect
    await entry1.subscribe(bus.ip, bus.port)
    await entry2.subscribe(bus.ip, bus.port)

    # Send message
    event = await entry2.emit("test", ExampleEvent("Hello"))

    # Assert
    assert event.id in entry1._received


async def test_extend_buses():

    # Create resources
    local_bus = EventBus()  # local machine
    remote_bus = EventBus()  # remote machine
    await local_bus.aserve()  # Start server
    await remote_bus.aserve()  # Start server

    # Connect via EntryPoint
    brige = EntryPoint("entry")
    await brige.subscribe(remote_bus.ip, remote_bus.port)

    # Extend
    await brige.extend("*", local_bus, Any)

    # Test
    remote_entry = EntryPoint("remote_entry")
    local_entry = EntryPoint("local_entry")

    await local_entry.local_subscribe(local_bus)
    await remote_entry.subscribe(remote_bus.ip, remote_bus.port)

    await local_entry.on("test", handler, ExampleEvent)
    event = await remote_entry.emit("test", ExampleEvent("Hello"))

    assert event.id in local_entry._received
