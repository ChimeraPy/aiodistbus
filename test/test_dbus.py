import logging
from typing import List

import pytest

from aiodistbus import DEntryPoint, Event

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

logger = logging.getLogger("aiodistbus")


async def test_dbus_instance(dbus):
    ...


async def test_dentrypoint_instance(dbus):
    entry = DEntryPoint()
    await entry.connect(dbus.ip, dbus.port)
    await entry.close()


async def test_dbus_connect(dbus, dentrypoints):

    # Create resources
    e1, e2 = dentrypoints

    # Add funcs
    await e1.on("test", func, ExampleEvent)

    # Connect
    await e1.connect(dbus.ip, dbus.port)
    await e2.connect(dbus.ip, dbus.port)


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
async def test_dbus_emit(dbus, dentrypoints, event_type, func, dtype, dtype_instance):

    # Create resources
    e1, e2 = dentrypoints

    # Add funcs
    await e1.on(event_type, func, dtype)

    # Connect
    await e1.connect(dbus.ip, dbus.port)
    await e2.connect(dbus.ip, dbus.port)

    # Send message
    event1 = await e2.emit(event_type, dtype_instance)

    # Need to flush
    await dbus.flush()

    # Assert
    assert event1 and event1.id in e1._received


@pytest.mark.parametrize(
    "event_type, func, dtype_instance",
    [
        ("test", func, ExampleEvent("Hello")),
        ("test_str", func_str, "Hello"),
        ("test_bytes", func_bytes, b"Hello"),
        ("test_list", func_list, ["Hello"]),
        ("test_int", func_int, 1),
        ("test_float", func_float, 1.0),
        ("test_bool", func_bool, True),
        ("test_none", func_none, None),
        ("test_dict", func_dict, {"hello": "world"}),
    ],
)
async def test_dbus_emit_without_specifying_dtype(
    dbus, dentrypoints, event_type, func, dtype_instance
):

    # Create resources
    e1, e2 = dentrypoints

    # Add funcs
    await e1.on(event_type, func)

    # Connect
    await e1.connect(dbus.ip, dbus.port)
    await e2.connect(dbus.ip, dbus.port)

    # Send message
    event1 = await e2.emit(event_type, dtype_instance)

    # Need to flush
    await dbus.flush()

    # Assert
    assert event1 and event1.id in e1._received


async def test_dbus_emit_null(dbus, dentrypoints):

    # Create resources
    e1, e2 = dentrypoints

    # Add funcs
    await e1.on("test", func_none)

    # Connect
    await e1.connect(dbus.ip, dbus.port)
    await e2.connect(dbus.ip, dbus.port)

    # Send message
    event1 = await e2.emit("test")

    # Need to flush
    await dbus.flush()

    # Assert
    assert event1 and event1.id in e1._received


@pytest.mark.parametrize(
    "wildcard, false_case, test_case",
    [
        ("*", "", "test"),
        ("test.*", "hello", "test.a"),
        ("test.test.*", "", "test.test.b"),
        ("test.test.*", "", "test.test.test.test.test"),
    ],
)
async def test_dbus_emit_wildcard(dbus, dentrypoints, wildcard, false_case, test_case):

    # Create resources
    e1, e2 = dentrypoints

    # Add funcs
    await e1.on(wildcard, wildcard_func, Event)

    # Connect
    await e1.connect(dbus.ip, dbus.port)
    await e2.connect(dbus.ip, dbus.port)

    # Send message
    event1 = None
    if false_case != "":
        event1 = await e2.emit(false_case, ExampleEvent("Hello"))
    event2 = await e2.emit(test_case, ExampleEvent("Goodbye"))

    # Need to flush
    await dbus.flush()

    # Assert
    if false_case != "":
        assert event1 and event1.id not in e1._received
    assert event2 and event2.id in e1._received


async def test_dbus_off(dbus, dentrypoints):

    # Create resources
    e1, e2 = dentrypoints

    # Add funcs
    await e1.on("test", func, ExampleEvent)

    # Connect
    await e1.connect(dbus.ip, dbus.port)
    await e2.connect(dbus.ip, dbus.port)

    # Off
    await e1.off("test")

    # Send message
    event1 = await e2.emit("test", ExampleEvent("Hello"))

    # Need to flush
    await dbus.flush()

    # Assert
    assert event1 and event1.id not in e1._received
