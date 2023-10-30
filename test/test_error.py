import asyncio
import logging
import os

import pytest

from aiodistbus import DEntryPoint, DEventBus

from .conftest import ExampleEvent, func

logger = logging.getLogger("aiodistbus")


class CrashDEventBus(DEventBus):
    async def close(self):

        if self._running:

            # IMITATE A CRASH
            # Inform to stop
            # event_d = Event("aiodistbus.eventbus.close").to_json().encode()
            # await self._emit(b"aiodistbus.eventbus.close", event_d)

            # Stop the main routine
            self._running = False
            await self.run_task

            # Stop the pulse
            await self.timer.stop()

            # Close sockets
            self.snapshot.close()
            self.publisher.close()
            self.collector.close()
            self.ctx.term()


def faulty_func(event: ExampleEvent):
    assert isinstance(event, ExampleEvent)
    logger.info(f"Received event {event}")
    raise RuntimeError("Oh snap, something failed :'(")


async def afaulty_func(event: ExampleEvent):
    assert isinstance(event, ExampleEvent)
    logger.info(f"Received event {event}")
    raise RuntimeError("Oh snap, something failed :'(")


################################################################################
## Tests
################################################################################


async def test_connect_timeout():
    e = DEntryPoint()
    with pytest.raises(asyncio.TimeoutError):
        await e.connect("127.0.0.1", port=5555, timeout=2)

    await e.close()


@pytest.mark.skip(reason="Passes locally, but not on CI")
async def test_pulse_crash_detection():
    crash_dbus = CrashDEventBus(ip="127.0.0.1", pulse=0.25)

    # Create resources
    e = DEntryPoint(pulse_ttl=1, pulse_limit=3)

    # Using flag to detect crash
    crash = False

    async def crash_detected():
        nonlocal crash
        crash = True

    # Connect
    await e.connect(crash_dbus.ip, crash_dbus.port, on_disrupt=crash_detected)

    # Normal operation
    await asyncio.sleep(1)

    # Simulate running and then crashing
    await crash_dbus.close()
    await asyncio.sleep(5)

    # Assert
    assert crash
    await e.close()


@pytest.mark.parametrize(
    "func",
    [
        faulty_func,
        afaulty_func,
    ],
)
async def test_exception_in_handler_with_bus(bus, entrypoints, func):

    # Create resources
    e1, e2 = entrypoints

    # Add funcs
    await e1.on("faulty", func, ExampleEvent)

    # Connect
    await e1.connect(bus)
    await e2.connect(bus)

    # Send message
    event = await e2.emit("faulty", ExampleEvent("hello"))

    # Assert
    assert event.id in e1._received
    assert len(e1._received) == 1


@pytest.mark.parametrize(
    "func",
    [
        faulty_func,
        afaulty_func,
    ],
)
async def test_exception_in_handler_with_dbus(dbus, dentrypoints, func):

    # Create resources
    e1, e2 = dentrypoints

    # Add funcs
    await e1.on("faulty", func, ExampleEvent)

    # Connect
    await e1.connect(dbus.ip, dbus.port)
    await e2.connect(dbus.ip, dbus.port)

    # Send message
    event = await e2.emit("faulty", ExampleEvent("hello"))

    # Flush
    await dbus.flush()

    # Assert
    assert event.id in e1._received
    assert len(e1._received) == 1


async def test_exception_in_encoder(dbus, dentrypoints):

    # Create resources
    e1, e2 = dentrypoints

    # Add funcs
    await e1.on("test", func, ExampleEvent)

    # Connect
    await e1.connect(dbus.ip, dbus.port)
    await e2.connect(dbus.ip, dbus.port)

    # Send message
    f = open("test.txt", "w")
    _ = await e2.emit("test", f)

    # Remove file
    try:
        os.remove("test.txt")
    except FileNotFoundError:
        pass

    # Flush
    await dbus.flush()


async def test_exception_in_decoder(dbus, dentrypoints):

    # Create resources
    e1, e2 = dentrypoints

    # Add funcs
    await e1.on("test", func, ExampleEvent)

    # Connect
    await e1.connect(dbus.ip, dbus.port)
    await e2.connect(dbus.ip, dbus.port)

    # Send message
    _ = await e2.emit("test", ["msg", "hello"])

    # Need to flush
    await dbus.flush()
