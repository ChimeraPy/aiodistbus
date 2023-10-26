import logging
from typing import List

import pytest

from aiodistbus import DEntryPoint, Event

from .conftest import (
    ExampleEvent,
    handler,
    handler_bool,
    handler_bytes,
    handler_dict,
    handler_float,
    handler_int,
    handler_list,
    handler_none,
    handler_str,
    wildcard_handler,
)

logger = logging.getLogger("aiodistbus")


async def test_dbus_instance(dbus):
    ...


async def test_dentrypoint_instance(dbus):
    entry = DEntryPoint()
    await entry.connect(dbus.ip, dbus.port)
    await entry.close()


@pytest.mark.parametrize(
    "event_type, handler, dtype, dtype_instance",
    [
        ("test", handler, ExampleEvent, ExampleEvent("Hello")),
        ("test_str", handler_str, str, "Hello"),
        ("test_bytes", handler_bytes, bytes, b"Hello"),
        ("test_list", handler_list, List, ["Hello"]),
        ("test_int", handler_int, int, 1),
        ("test_float", handler_float, float, 1.0),
        ("test_bool", handler_bool, bool, True),
        ("test_none", handler_none, None, None),
        ("test_dict", handler_dict, dict, {"hello": "world"}),
    ],
)
async def test_local_bus(bus, entrypoints, event_type, handler, dtype, dtype_instance):

    # Create resources
    e1, e2 = entrypoints

    # Add handlers
    await e1.on(event_type, handler, dtype)

    # Connect
    await e1.connect(bus)
    await e2.connect(bus)

    # Send message
    event = await e2.emit(event_type, dtype_instance)

    # Assert
    assert event.id in e1._received
    assert len(e1._received) == 1


async def test_local_bus_wildcard(bus, entrypoints):

    # Create resources
    e1, e2 = entrypoints

    # Add handlers
    await e1.on("test.*", wildcard_handler, Event)

    # Connect
    await e1.connect(bus)
    await e2.connect(bus)

    # Send message
    event = await e2.emit("test.hello", ExampleEvent("Hello"))

    # Assert
    assert event.id in e1._received
    assert len(e1._received) == 1


async def test_dbus_connect(dbus, dentrypoints):

    # Create resources
    e1, e2 = dentrypoints

    # Add handlers
    await e1.on("test", handler, ExampleEvent)

    # Connect
    await e1.connect(dbus.ip, dbus.port)
    await e2.connect(dbus.ip, dbus.port)


@pytest.mark.parametrize(
    "event_type, handler, dtype, dtype_instance",
    [
        ("test", handler, ExampleEvent, ExampleEvent("Hello")),
        ("test_str", handler_str, str, "Hello"),
        ("test_bytes", handler_bytes, bytes, b"Hello"),
        ("test_list", handler_list, List, ["Hello"]),
        ("test_int", handler_int, int, 1),
        ("test_float", handler_float, float, 1.0),
        ("test_bool", handler_bool, bool, True),
        ("test_none", handler_none, None, None),
        ("test_dict", handler_dict, dict, {"hello": "world"}),
    ],
)
async def test_dbus_emit(
    dbus, dentrypoints, event_type, handler, dtype, dtype_instance
):

    # Create resources
    e1, e2 = dentrypoints

    # Add handlers
    await e1.on(event_type, handler, dtype)

    # Connect
    await e1.connect(dbus.ip, dbus.port)
    await e2.connect(dbus.ip, dbus.port)

    # Send message
    event1 = await e2.emit(event_type, dtype_instance)

    # Need to flush
    await dbus.flush()

    # Assert
    assert event1 and event1.id in e1._received


async def test_dbus_emit_wildcard(dbus, dentrypoints):

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


@pytest.mark.parametrize(
    "event_type, handler, dtype, dtype_instance",
    [
        ("test", handler, ExampleEvent, ExampleEvent("Hello")),
        ("test_str", handler_str, str, "Hello"),
        ("test_bytes", handler_bytes, bytes, b"Hello"),
        ("test_list", handler_list, List, ["Hello"]),
        ("test_int", handler_int, int, 1),
        ("test_float", handler_float, float, 1.0),
        ("test_bool", handler_bool, bool, True),
        ("test_none", handler_none, None, None),
        ("test_dict", handler_dict, dict, {"hello": "world"}),
    ],
)
async def test_bridge_bus_to_dbus(
    bus, dbus, entrypoints, dentrypoints, event_type, handler, dtype, dtype_instance
):

    # Create resources
    e1, _ = entrypoints
    de1, _ = dentrypoints

    # Add handlers
    await de1.on(event_type, handler, dtype)

    # Connect entrypoint to bus
    await e1.connect(bus)
    await de1.connect(dbus.ip, dbus.port)

    # Bridge
    await bus.forward(dbus.ip, dbus.port)

    # Send message
    event = await e1.emit(event_type, dtype_instance)

    # Need to flush
    await dbus.flush()

    # Assert
    assert event.id in de1._received


@pytest.mark.parametrize(
    "event_type, handler, dtype, dtype_instance",
    [
        ("test", handler, ExampleEvent, ExampleEvent("Hello")),
        ("test_str", handler_str, str, "Hello"),
        ("test_bytes", handler_bytes, bytes, b"Hello"),
        ("test_list", handler_list, List, ["Hello"]),
        ("test_int", handler_int, int, 1),
        ("test_float", handler_float, float, 1.0),
        ("test_bool", handler_bool, bool, True),
        ("test_none", handler_none, None, None),
        ("test_dict", handler_dict, dict, {"hello": "world"}),
    ],
)
async def test_bridge_dbus_to_bus(
    bus, dbus, entrypoints, dentrypoints, event_type, handler, dtype, dtype_instance
):

    # Create resources
    e1, _ = entrypoints
    de1, _ = dentrypoints

    # Add handlers
    await e1.on(event_type, handler, dtype)

    # Connect entrypoint to bus
    await e1.connect(bus)
    await de1.connect(dbus.ip, dbus.port)

    # Bridge
    await dbus.forward(bus)

    # Send message
    event = await de1.emit(event_type, dtype_instance)

    # Need to flush
    await dbus.flush()

    # Assert
    assert event.id in e1._received
