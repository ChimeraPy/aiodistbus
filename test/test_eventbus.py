import asyncio
import logging
from dataclasses import dataclass

import pytest
from dataclasses_json import DataClassJsonMixin

from aiodistbus import DEntryPoint, DEventBus, EntryPoint, Event, EventBus

logger = logging.getLogger("aiodistbus")


@dataclass
class ExampleEvent(DataClassJsonMixin):
    msg: str


async def handler(event: ExampleEvent):
    logger.info(f"Received event {event}")


async def wildcard_handler(event: Event):
    logger.info(f"Received event {event}")


@pytest.fixture
async def bus():
    bus = EventBus()
    yield bus
    await bus.close()


@pytest.fixture
async def dbus():
    bus = DEventBus(ip="127.0.0.1", port=5555)
    yield bus
    await bus.close()


async def test_deventbus_instance(dbus):
    ...


async def test_dentrypoint_instance(dbus):
    entry = DEntryPoint()
    await entry.connect(dbus.ip, dbus.port)
    await entry.close()


async def test_local_eventbus(bus):

    # Create resources
    entry1 = EntryPoint()
    entry2 = EntryPoint()

    # Add handlers
    await entry1.on("test", handler, ExampleEvent)
    await entry1.on("hello", handler, ExampleEvent)
    await entry1.on("test.hello", handler, ExampleEvent)

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


async def test_local_eventbus_wildcard(bus):

    # Create resources
    entry1 = EntryPoint()
    entry2 = EntryPoint()

    # Add handlers
    await entry1.on("test.*", wildcard_handler, Event)

    # Connect
    await entry1.connect(bus)
    await entry2.connect(bus)

    # Send message
    event = await entry2.emit("test.a", ExampleEvent("Hello"))

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


async def test_remote_eventbus_emit(dbus):

    # Create resources
    entry1 = DEntryPoint()
    entry2 = DEntryPoint()

    # Add handlers
    await entry1.on("test", handler, ExampleEvent)

    # Connect
    await entry1.connect(dbus.ip, dbus.port)
    await entry2.connect(dbus.ip, dbus.port)

    # Send message
    event1 = await entry2.emit("test", ExampleEvent("Hello"))

    # Need to flush
    await dbus.flush()

    # Assert
    assert event1 and event1.id in entry1._received
    await entry1.close()
    await entry2.close()


async def test_remote_eventbus_emit_wildcard(dbus):

    # Create resources
    entry1 = DEntryPoint()
    entry2 = DEntryPoint()

    # Add handlers
    await entry1.on("test", handler, ExampleEvent)
    await entry1.on("test.*", wildcard_handler, Event)

    # Connect
    await entry1.connect(dbus.ip, dbus.port)
    await entry2.connect(dbus.ip, dbus.port)

    # Send message
    event1 = await entry2.emit("hello", ExampleEvent("Hello"))
    event2 = await entry2.emit("test.b", ExampleEvent("Goodbye"))

    # Need to flush
    await dbus.flush()

    # Assert
    assert event1 and event1.id not in entry1._received
    assert event2 and event2.id in entry1._received
    await entry1.close()
    await entry2.close()
