import asyncio

import pytest

from aiodistbus import DEntryPoint, DEventBus


@pytest.mark.repeat(10)
async def test_create_dbus():
    bus = DEventBus("127.0.0.1")
    await asyncio.wait_for(bus.close(), timeout=3)


@pytest.mark.repeat(10)
async def test_dbus_entrypoint():
    bus = DEventBus("127.0.0.1")
    e = DEntryPoint()
    await e.connect(bus.ip, bus.port)
    await asyncio.wait_for(bus.close(), timeout=3)
    await asyncio.wait_for(e.close(), timeout=3)


@pytest.mark.repeat(10)
async def test_entrypoint_dbus():
    bus = DEventBus("127.0.0.1")
    e = DEntryPoint()
    await e.connect(bus.ip, bus.port)
    await asyncio.wait_for(e.close(), timeout=3)
    await asyncio.wait_for(bus.close(), timeout=3)
