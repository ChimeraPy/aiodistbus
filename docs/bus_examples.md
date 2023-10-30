# Local EventBus & EntryPoint

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
