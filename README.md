![ChimeraPy/aiodistbus](https://github.com/ChimeraPy/aiodistbus/assets/40870026/306bff08-612c-4cc2-8354-e2407a4c9de1)
<p align="center">
    <em>A Distributed Eventbus using ZeroMQ and AsyncIO for Python.</em>
</p>
<p align="center">
<a href="https://github.com/ChimeraPy/aiodistbus/actions?query=workflow%3ATest" target="_blank">
    <img src="https://github.com/ChimeraPy/aiodistbus/workflows/Test/badge.svg" alt="Test">
</a>

<a href='https://coveralls.io/github/ChimeraPy/aiodistbus?branch=main'>
    <img src='https://coveralls.io/repos/github/ChimeraPy/aiodistbus/badge.svg?branch=main' alt='Coverage Status' />
</a>
</p>

The objective of this library is to provide both a local and distributed eventbus that are compatible to communicate. A similar API can be used in both versions of the eventbuses implementations.

## Installation

For installing the package, download from PyPI and install with ``pip``:

```bash
pip install aiodistbus
```

Here is a link to the [Documentation](https://aiodistbus.readthedocs.io/en/latest/). If you encounter any issues in terms of code or documentation, please don't hesitate to make an issue.

## EventBus Example

The eventbus implementation follows a client-server design approach, with the ``DEventBus`` as the server and ``DEntryPoint`` as the client. Here is a quick example to emit an event.

```python
import asyncio
from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin # DO NOT FORGET THIS!

import aiodistbus as adb

@dataclass
class ExampleEvent(DataClassJsonMixin): # NEEDS TO BE A DataClassJsonMixin!
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

if __name__ == '__main__':
    asyncio.run(main())
```

## Design

In the ``aiodistbus`` library, we provided 2 eventbus implementations: ``EventBus`` and ``DEventBus``. The ``EventBus`` class is for local (within same Python runtime) observer pattern. In the other hand, ``DEventBus`` class is for a distributed eventbus that leverages ZeroMQ -- closing following the [Clone pattern](https://zguide.zeromq.org/docs/chapter5/).

The Clone pattern uses a client-server structure, where a centralized broker broadcasts messages sent by clients. As described in the ZeroMQ Guide, this creates a single point of failure, but yields in a simpler and more scalable implementation.

## Contributing
Contributions are welcomed! Our [Developer Documentation](https://chimerapy.readthedocs.io/en/latest/developer/index.html) should provide more details in how ChimeraPy works and what is in current development.

## License
[ChimeraPy](https://github.com/ChimeraPy) and [ChimeraPy/aiodistbus](https://github.com/ChimeraPy/aiodistbus) uses the GNU GENERAL PUBLIC LICENSE, as found in [LICENSE](./LICENSE) file.

## Funding Info
This project is supported by the [National Science Foundation](https://www.nsf.gov/) under AI Institute  Grant No. [DRL-2112635](https://www.nsf.gov/awardsearch/showAward?AWD_ID=2112635&HistoricalAwards=false).
