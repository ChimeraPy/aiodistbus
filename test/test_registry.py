import logging
from typing import List

import pytest

from aiodistbus import Event, registry

from .conftest import ExampleEvent

logger = logging.getLogger("aiodistbus")


@registry.on("test", ExampleEvent)
async def func(event: ExampleEvent):
    assert isinstance(event, ExampleEvent)
    logger.info(f"Received event {event}")


@registry.on("test_str", str)
async def func_str(event: str):
    assert isinstance(event, str)
    logger.info(f"Received event {event}")


@registry.on("test_bytes", bytes)
async def func_bytes(event: bytes):
    assert isinstance(event, bytes)
    logger.info("Received event %s", event.decode("utf-8"))


@registry.on("test_int", int)
async def func_int(event: int):
    assert isinstance(event, int)
    logger.info(f"Received event {event}")


@registry.on("test_float", float)
async def func_float(event: float):
    assert isinstance(event, float)
    logger.info(f"Received event {event}")


@registry.on("test_bool", bool)
async def func_bool(event: bool):
    assert isinstance(event, bool)
    logger.info(f"Received event {event}")


@registry.on("test_none")
async def func_none():
    logger.info("Received event for None")


@registry.on("test_dict", dict)
async def func_dict(event: dict):
    assert isinstance(event, dict)
    logger.info(f"Received event {event}")


@registry.on("test_list", List)
async def func_list(event: List[str]):
    assert isinstance(event, List)
    logger.info(f"Received event {event}")


@registry.on("*", Event)
async def wildcard_func(event: Event):
    assert isinstance(event, Event)
    logger.info(f"Received event {event}")


class ExampleClass:
    def __init__(self):
        self.a = 1

    @registry.on("setup", namespace="ExampleClass")
    async def setup(self):
        logger.debug(f"Setup called: {self.a}")

    @registry.on("start", namespace="ExampleClass")
    def start(self):
        logger.debug(f"Start called: {self.a}")


@pytest.mark.parametrize(
    "event_type",
    [
        "test",
        "test_str",
        "test_bytes",
        "test_int",
        "test_float",
        "test_bool",
        "test_none",
        "test_dict",
    ],
)
async def test_registry(event_type: str):
    assert event_type in registry.get_handlers("default")


@pytest.mark.parametrize(
    "event_type, dtype_instance",
    [
        ("test", ExampleEvent("Hello")),
        ("test_str", "Hello"),
        ("test_bytes", b"Hello"),
        ("test_list", ["Hello"]),
        ("test_int", 1),
        ("test_float", 1.0),
        ("test_bool", True),
        ("test_none", None),
        ("test_dict", {"hello": "world"}),
    ],
)
async def test_bus_registry(bus, entrypoints, event_type, dtype_instance):
    # Create resources
    e1, e2 = entrypoints

    # Add handlers
    await e1.use(registry)

    # Connect
    await e1.connect(bus)
    await e2.connect(bus)

    # Send message
    event = await e2.emit(event_type, dtype_instance)

    # Assert
    assert event.id in e1._received


@pytest.mark.parametrize(
    "event_type, dtype_instance",
    [
        ("test", ExampleEvent("Hello")),
        ("test_str", "Hello"),
        ("test_bytes", b"Hello"),
        ("test_list", ["Hello"]),
        ("test_int", 1),
        ("test_float", 1.0),
        ("test_bool", True),
        ("test_none", None),
        ("test_dict", {"hello": "world"}),
    ],
)
async def test_dbus_registry(dbus, dentrypoints, event_type, dtype_instance):
    # Create resources
    e1, e2 = dentrypoints

    # Add handlers
    await e1.use(registry)

    # Connect
    await e1.connect(dbus.ip, dbus.port)
    await e2.connect(dbus.ip, dbus.port)

    # Send message
    event = await e2.emit(event_type, dtype_instance)

    # Flush
    await dbus.flush()

    # Assert
    assert event.id in e1._received


async def test_registry_class(bus, entrypoints):

    # Resources
    e1, e2 = entrypoints

    # Connect to bus
    await e1.connect(bus)
    await e2.connect(bus)

    # Setup the handlers
    instance = ExampleClass()
    await e1.use(registry, b_args=[instance], namespace="ExampleClass")

    # Emit the event
    event1 = await e2.emit("setup")
    event2 = await e2.emit("start")

    # Asserts
    assert event1.id in e1._received
    assert event2.id in e1._received
