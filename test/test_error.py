import asyncio
import logging

import pytest

from aiodistbus import DEntryPoint, DEventBus

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
            # self.ctx.term()


@pytest.mark.repeat(10)
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
    await asyncio.sleep(5)

    # Assert
    # assert crash

    await crash_dbus.close()
    await e.close()

    logger.debug(f"CRASH: {crash}")
