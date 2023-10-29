import asyncio
import logging
import multiprocessing as mp
from typing import List

import pytest

from aiodistbus import DEntryPoint

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
    linux_run_only,
)

logger = logging.getLogger("aiodistbus")


def subprocess_dentrypoint(ip, port, event_type, dtype_instance):
    async def main():

        # Create resources
        e1 = DEntryPoint()
        await e1.connect(ip, port)

        # Emit
        await e1.emit(event_type, dtype_instance)

        # Close
        await e1.close()

    asyncio.run(main())


@linux_run_only
@pytest.mark.parametrize("ctx_str", ["fork", "spawn"])
async def test_dbus_mp_ctx(dbus, dentrypoints, ctx_str):

    # Create resources
    e1, _ = dentrypoints

    # Add funcs
    await e1.on("test", func, ExampleEvent)

    # Connect
    await e1.connect(dbus.ip, dbus.port)

    # Create entrypoint in a subprocess
    ctx = mp.get_context(ctx_str)
    p = ctx.Process(
        target=subprocess_dentrypoint,
        args=(dbus.ip, dbus.port, "test", ExampleEvent("Hello")),
    )
    p.start()

    # Need to flush
    await dbus.flush()
    p.join()

    # Assert
    assert len(e1._received) != 0
