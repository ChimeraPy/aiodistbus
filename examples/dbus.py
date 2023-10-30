import asyncio
from dataclasses import dataclass

from dataclasses_json import DataClassJsonMixin  # DO NOT FORGET THIS!

import aiodistbus as adb


@dataclass
class ExampleEvent(DataClassJsonMixin):  # NEEDS TO BE A DataClassJsonMixin!
    msg: str


async def handler(event: ExampleEvent):
    print(event)


async def main():
    # Create resources
    bus, e1, e2 = adb.DEventBus(), adb.DEntryPoint(), adb.DEntryPoint()

    # Connect
    await e1.connect(bus.ip, bus.port)
    await e2.connect(bus.ip, bus.port)

    # Add funcs
    await e1.on("test", handler, ExampleEvent)

    # Send message
    await e2.emit("test", ExampleEvent("hello"))

    # Flush
    await bus.flush()

    # Close resources
    await e1.close()
    await e2.close()
    await bus.close()


if __name__ == "__main__":
    asyncio.run(main())
