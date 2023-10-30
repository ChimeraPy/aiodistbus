# aiodistbus
A Distributed Eventbus using ZeroMQ and asyncio

# Installation

For installing the package, download from PYPI and install with ``pip``:

```bash
pip install aiodistbus
```

# Useage

In the ``aiodistbus`` library, we provided 2 eventbus implementations: ``EventBus`` and ``DEventBus``. The ``EventBus`` class is for local (within same Python runtime) observer pattern. In the other hand, ``DEventBus`` class is for a distributed eventbus that leverages ZeroMQ -- closing following the [Clone pattern](https://zguide.zeromq.org/docs/chapter5/).

The Clone pattern uses a client-server structure, where a centralized broker broadcasts messages sent by clients. As described in the ZeroMQ Guide, this creates a single point of failure, but yields in a simpler and more scalable implementation.

## Event Subscriptions

The front-facing API of both ``(EventBus, EntryPoint)`` and ``(DEventBus, DEntryPoint)`` are identifical, but important differences need to be consider. For a distributed configuration, ensure that any emitted ``Event`` data is serializable -- this is not a requirement for local setup.

```python
from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin
from aiodistbus import EntryPoint, EventBus # or DEntryPoint, DEventBus

@dataclass
class ExampleEvent(DataClassJsonMixin):
    msg: str

async def handler(event: ExampleEvent):
    assert isinstance(event, ExampleEvent)
    logger.info(f"Received event {event}")

# Create resources
bus = EventBus() # of DEventBus for distributed eventbus
e1, e2 = EntryPoint(), EntryPoint() # or DEntryPoint for distributed eventbus

# Add handlers
await e1.on('example', handler, ExampleEvent)

# Connect
await e1.connect(bus)
await e2.connect(bus)

# Send message and e1's handler is executed
event = await e2.emit('example', ExampleEvent(msg="hello"))

# Closing (order doesn't matter)
await bus.close()
await e1.close()
await e2.close()
```

## Bridge between Local and Distributed

This is TODO

# TODO
 - [x] Disconnect operation
 - [x] Bridge Implementation
 - [x] Removing dead subscribers
 - [x] Heartbeat with handler
 - [x] Decorator Implementation (with Namespace)
 - [x] Error handling
 - [x] Multiprocessing testing
 - [x] Message Hashsum
 - [x] Dataclass Decorator
 - [x] Debounding option
 - [ ] Connect Timeout Exception
 - [ ] Stress testing
 - [ ] Automated testing via GitHub actions
 - [ ] Rerun pre-commit on all files
 - [ ] Improve documentation
