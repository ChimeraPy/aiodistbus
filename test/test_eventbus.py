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
    assert isinstance(event, ExampleEvent)
    logger.info(f"Received event {event}")


async def wildcard_handler(event: Event):
    assert isinstance(event, Event)
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


@pytest.fixture
async def entrypoints():
    e1 = EntryPoint()
    e2 = EntryPoint()
    yield e1, e2
    await e1.close()
    await e2.close()


@pytest.fixture
async def dentrypoints():
    e1 = DEntryPoint()
    e2 = DEntryPoint()
    yield e1, e2
    await e1.close()
    await e2.close()


async def test_deventbus_instance(dbus):
    ...


async def test_dentrypoint_instance(dbus):
    entry = DEntryPoint()
    await entry.connect(dbus.ip, dbus.port)
    await entry.close()


async def test_local_eventbus(bus, entrypoints):

    # Create resources
    e1, e2 = entrypoints

    # Add handlers
    await e1.on("test", handler, ExampleEvent)
    await e1.on("hello", handler, ExampleEvent)
    await e1.on("test.hello", handler, ExampleEvent)

    # Connect
    await e1.connect(bus)
    await e2.connect(bus)

    # Send message
    event = await e2.emit("test", ExampleEvent("Hello"))

    # Assert
    assert event.id in e1._received
    assert len(e1._received) == 1


async def test_local_eventbus_wildcard(bus, entrypoints):

    # Create resources
    e1, e2 = entrypoints

    # Add handlers
    await e1.on("test.*", wildcard_handler, Event)

    # Connect
    await e1.connect(bus)
    await e2.connect(bus)

    # Send message
    event = await e2.emit("test.a", ExampleEvent("Hello"))

    # Assert
    assert event.id in e1._received
    assert len(e1._received) == 1


async def test_remote_eventbus_connect(dbus, dentrypoints):

    # Create resources
    e1, e2 = dentrypoints

    # Add handlers
    await e1.on("test", handler, ExampleEvent)

    # Connect
    await e1.connect(dbus.ip, dbus.port)
    await e2.connect(dbus.ip, dbus.port)


async def test_remote_eventbus_emit(dbus, dentrypoints):

    # Create resources
    e1, e2 = dentrypoints

    # Add handlers
    await e1.on("test", handler, ExampleEvent)

    # Connect
    await e1.connect(dbus.ip, dbus.port)
    await e2.connect(dbus.ip, dbus.port)

    # Send message
    event1 = await e2.emit("test", ExampleEvent("Hello"))

    # Need to flush
    await dbus.flush()

    # Assert
    assert event1 and event1.id in e1._received


async def test_remote_eventbus_emit_wildcard(dbus, dentrypoints):

    # Create resources
    e1, e2 = dentrypoints

    # Add handlers
    await e1.on("test", handler, ExampleEvent)
    await e1.on("test.*", wildcard_handler, Event)

    # Connect
    await e1.connect(dbus.ip, dbus.port)
    await e2.connect(dbus.ip, dbus.port)

    # Send message
    event1 = await e2.emit("hello", ExampleEvent("Hello"))
    event2 = await e2.emit("test.b", ExampleEvent("Goodbye"))

    # Need to flush
    await dbus.flush()

    # Assert
    assert event1 and event1.id not in e1._received
    assert event2 and event2.id in e1._received
