# Local EventBus & EntryPoint

For a local eventbus implementation, the API and configuration is similar to the their distributed counterparts. Key note here is that serialization is not necessary but recommended -- in case you are briding messages between eventbuses.

First, our imports are for specifically the local versions:

```python
from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin
from aiodistbus import EntryPoint, EventBus
```

Then we add the handler and the data type (it can be anything serializable) that is going to be the handler's input.

```python
@dataclass
class ExampleEvent(DataClassJsonMixin):
    msg: str

async def handler(event: ExampleEvent):
    assert isinstance(event, ExampleEvent)
    logger.info(f"Received event {event}")
```

After the configuration, we have to create the necessary server-client resources and connect the setup:

```python
# Create resources
bus = EventBus()
e1, e2 = EntryPoint(), EntryPoint()

# Add handlers
await e1.on('example', handler, ExampleEvent)

# Connect
await e1.connect(bus)
await e2.connect(bus)
```

With everything configured, we can not emit messages between the entrypoints:

```python
# Send message and e1's handler is executed
event = await e2.emit('example', ExampleEvent(msg="hello"))
```

Make sure to close the resources at the end of the program.

```python
# Closing (order doesn't matter)
await bus.close()
await e1.close()
await e2.close()
```
