from typing import List

import pytest

from .conftest import (
    ExampleEvent,
    func,
    func_bool,
    func_bytes,
    func_dict,
    func_float,
    func_int,
    func_list,
    func_none,
    func_str,
)


@pytest.mark.parametrize(
    "event_type, func, dtype, dtype_instance",
    [
        ("test", func, ExampleEvent, ExampleEvent("Hello")),
        ("test_str", func_str, str, "Hello"),
        ("test_bytes", func_bytes, bytes, b"Hello"),
        ("test_list", func_list, List, ["Hello"]),
        ("test_int", func_int, int, 1),
        ("test_float", func_float, float, 1.0),
        ("test_bool", func_bool, bool, True),
        ("test_none", func_none, None, None),
        ("test_dict", func_dict, dict, {"hello": "world"}),
    ],
)
async def test_bridge_bus_to_dbus(
    bus, dbus, entrypoints, dentrypoints, event_type, func, dtype, dtype_instance
):

    # Create resources
    e1, _ = entrypoints
    de1, _ = dentrypoints

    # Add funcs
    await de1.on(event_type, func, dtype)

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
    "event_type, func, dtype, dtype_instance",
    [
        ("test", func, ExampleEvent, ExampleEvent("Hello")),
        ("test_str", func_str, str, "Hello"),
        ("test_bytes", func_bytes, bytes, b"Hello"),
        ("test_list", func_list, List, ["Hello"]),
        ("test_int", func_int, int, 1),
        ("test_float", func_float, float, 1.0),
        ("test_bool", func_bool, bool, True),
        ("test_none", func_none, None, None),
        ("test_dict", func_dict, dict, {"hello": "world"}),
    ],
)
async def test_bridge_dbus_to_bus(
    bus, dbus, entrypoints, dentrypoints, event_type, func, dtype, dtype_instance
):

    # Create resources
    e1, _ = entrypoints
    de1, _ = dentrypoints

    # Add funcs
    await e1.on(event_type, func, dtype)

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
