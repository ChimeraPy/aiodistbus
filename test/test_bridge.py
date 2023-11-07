from typing import List

import pytest

from aiodistbus import DEventBus, EntryPoint, EventBus

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
        ("test.spaces", func, ExampleEvent, ExampleEvent(msg="world")),
    ],
)
async def test_forward_bus_to_dbus(
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
async def test_forward_dbus_to_bus(
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
async def test_bus_listen_to_dbus(
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
    await bus.listen(dbus.ip, dbus.port, event_types=[event_type])

    # Send message
    event = await de1.emit(event_type, dtype_instance)

    # Need to flush
    await dbus.flush()

    # Assert
    assert event.id in e1._received


async def test_bus_listen_to_dbus_wildcard(bus, dbus, entrypoints, dentrypoints):

    # Create resources
    e1, _ = entrypoints
    de1, _ = dentrypoints

    # Add funcs
    await e1.on("test", func)

    # Connect entrypoint to bus
    await e1.connect(bus)
    await de1.connect(dbus.ip, dbus.port)

    # Bridge
    await bus.listen(dbus.ip, dbus.port)

    # Send message
    event = await de1.emit("test", ExampleEvent("Hello"))

    # Need to flush
    await dbus.flush()

    # Assert
    assert event.id in e1._received


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
async def test_local_buses_comms_server_to_client(
    event_type, func, dtype, dtype_instance
):

    # Local buses
    sb = EventBus()
    sdbus = DEventBus()
    cb = EventBus()

    # Create entrypoint
    ce = EntryPoint()
    await ce.connect(cb)
    await ce.on(event_type, func, dtype)
    se = EntryPoint()
    await se.connect(sb)

    # Link
    await sb.forward(sdbus.ip, sdbus.port)
    await cb.listen(sdbus.ip, sdbus.port)

    # Send message
    event = await se.emit(event_type, dtype_instance)

    # Flush
    await sdbus.flush()

    # Assert
    assert event and event.id in ce._received


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
async def test_local_buses_comms_client_to_server(
    event_type, func, dtype, dtype_instance
):

    # Local buses
    sb = EventBus()
    sdbus = DEventBus()
    cb = EventBus()

    # Create entrypoint
    ce = EntryPoint()
    await ce.connect(cb)
    se = EntryPoint()
    await se.connect(sb)
    await se.on(event_type, func, dtype)

    # Link
    await cb.forward(sdbus.ip, sdbus.port)
    await sdbus.forward(sb)

    # Send message
    event = await ce.emit(event_type, dtype_instance)

    # Flush
    await sdbus.flush()

    # Assert
    assert event and event.id in se._received


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
async def test_local_buses_comms_bidirectional(event_type, func, dtype, dtype_instance):

    # Local buses
    sb = EventBus()
    sdbus = DEventBus()
    cb = EventBus()

    # Create entrypoint
    ce = EntryPoint()
    await ce.connect(cb)
    await ce.on(f"server.{event_type}", func, dtype)
    se = EntryPoint()
    await se.connect(sb)
    await se.on(f"client.{event_type}", func, dtype)

    # Link
    await cb.link(sdbus.ip, sdbus.port, ["client.*"], ["server.*"])
    await sb.link(sdbus.ip, sdbus.port, ["server.*"], ["client.*"])

    # Send message
    cevent = await ce.emit(f"client.{event_type}", dtype_instance)
    sevent = await se.emit(f"server.{event_type}", dtype_instance)

    # Flush
    await sdbus.flush()

    # Assert
    assert cevent and cevent.id in se._received
    assert sevent and sevent.id in ce._received
