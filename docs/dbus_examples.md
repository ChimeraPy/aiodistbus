# Distributed EventBus & DEntryPoint

For the distributed eventbus implementation, the data transmitted within the bus needs to be serializable.

!!! note
    Make sure to use ``DataClassJsonMixin`` when using a ``dataclass`` to permit the serialization of the data and documenting the dtypes.

```python
from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin
from aiodistbus import DEntryPoint, DEventBus
```

The handlers for events is the same as the local eventbus implementation, making interoperability feasible.

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
dbus = DEventBus()
e1, e2 = DEntryPoint(), DEntryPoint()

# Add handlers
await e1.on('example', handler, ExampleEvent)

# Connect
await e1.connect(dbus.ip, dbus.port)
await e2.connect(dbus.ip, dbus.port)
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
