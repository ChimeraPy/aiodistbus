from typing import List

import pytest

from aiodistbus import Event

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
    wildcard_func,
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
async def test_local_bus(bus, entrypoints, event_type, func, dtype, dtype_instance):

    # Create resources
    e1, e2 = entrypoints

    # Add funcs
    await e1.on(event_type, func, dtype)

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

    # Add funcs
    await e1.on("test.*", wildcard_func, Event)

    # Connect
    await e1.connect(bus)
    await e2.connect(bus)

    # Send message
    event = await e2.emit("test.hello", ExampleEvent("Hello"))

    # Assert
    assert event.id in e1._received
    assert len(e1._received) == 1


async def test_local_bus_off(bus, entrypoints):

    # Create resources
    e1, e2 = entrypoints

    # Add funcs
    await e1.on("test", func, ExampleEvent)

    # Connect
    await e1.connect(bus)
    await e2.connect(bus)

    # Remove
    await e1.off("test")

    # Send message
    event = await e2.emit("test", ExampleEvent("Hello"))

    # Assert
    assert event.id not in e1._received
    assert len(e1._received) == 0
