import logging
from dataclasses import dataclass
from typing import Any

import pytest

from aiodistbus import DEntryPoint, DEventBus, EntryPoint, EventBus

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


@pytest.fixture
async def dbus():
    bus = DEventBus(port=5555)
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


async def test_remote_eventbus_connect(dbus):

    # Create resources
    entry1 = DEntryPoint()
    entry2 = DEntryPoint()

    # Add handlers
    await entry1.on("test", handler, ExampleEvent)

    # Connect
    await entry1.connect(dbus.ip, dbus.port)
    await entry2.connect(dbus.ip, dbus.port)

    # Assert
    await entry1.close()
    await entry2.close()


async def test_remote_eventbus(dbus):

    # Create resources
    entry1 = DEntryPoint()
    entry2 = DEntryPoint()

    # Add handlers
    await entry1.on("test", handler, ExampleEvent)

    # Connect
    await entry1.connect(dbus.ip, dbus.port)
    await entry2.connect(dbus.ip, dbus.port)

    # Send message
    event = await entry2.emit("test", ExampleEvent("Hello"))

    # Assert
    assert event.id in entry1._received
    await entry1.close()
    await entry2.close()
