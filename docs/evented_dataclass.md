# Registry: Event Handler Decorator

To link the handlers to event types in a more streamline fashion, we can use a ``Registry`` to have ``Namespaces`` decided to list of handlers and their event types.

Here we perform the imports and configuration with the registry

```python
from aiodistbus import Event, registry

@dataclass
class ExampleEvent:
    msg: str

@registry.on("test", ExampleEvent)
async def func(event: ExampleEvent):
    assert isinstance(event, ExampleEvent)
    print(event)
```

Then we create the resources and leverage the ``use`` method of the ``EntryPoint`` to access the stored handler/event_type pairs.

```python
# Create resources
e1, e2 = entrypoints

# Add handlers
await e1.use(registry)

# Connect
await e1.connect(bus)
await e2.connect(bus)

# Send message
event = await e2.emit(event_type, dtype_instance)
```

The reason for a registry instead of a ``@ee.on('test', handler)``, like ``pyee``'s ``EventEmitter``, aproach is because in a multiprocessing context, a global eventbus or entrypoint isn't not going to work properly accross different multiprocessing context -- especially Windows's "spawn".
