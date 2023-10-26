import logging
from typing import List

import pytest

from aiodistbus import Event, registry

from .conftest import ExampleEvent

logger = logging.getLogger("aiodistbus")


@registry.on("test", ExampleEvent)
async def handler(event: ExampleEvent):
    assert isinstance(event, ExampleEvent)
    logger.info(f"Received event {event}")


@registry.on("test_str", str)
async def handler_str(event: str):
    assert isinstance(event, str)
    logger.info(f"Received event {event}")


@registry.on("test_bytes", bytes)
async def handler_bytes(event: bytes):
    assert isinstance(event, bytes)
    logger.info(f"Received event {event}")


@registry.on("test_int", int)
async def handler_int(event: int):
    assert isinstance(event, int)
    logger.info(f"Received event {event}")


@registry.on("test_float", float)
async def handler_float(event: float):
    assert isinstance(event, float)
    logger.info(f"Received event {event}")


@registry.on("test_bool", bool)
async def handler_bool(event: bool):
    assert isinstance(event, bool)
    logger.info(f"Received event {event}")


@registry.on("test_none")
async def handler_none():
    logger.info(f"Received event for None")


@registry.on("test_dict", dict)
async def handler_dict(event: dict):
    assert isinstance(event, dict)
    logger.info(f"Received event {event}")


@registry.on("test_list", List)
async def handler_list(event: List[str]):
    assert isinstance(event, List)
    logger.info(f"Received event {event}")


@registry.on("*", Event)
async def wildcard_handler(event: Event):
    assert isinstance(event, Event)
    logger.info(f"Received event {event}")


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
async def test_local_bus(bus, entrypoints, event_type, dtype_instance):
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
