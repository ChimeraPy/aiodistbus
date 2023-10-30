# Briding EventBuses

To make the handling of incoming messages from a distributed eventbus, a local eventbus is a good approach to perform separation-of-concerns.

## Local to Distributed

Once you create the eventbuses, the IP and port of the distributed eventbus is required to connect and emit messages to the distributed eventbus cluster.

```python
# Create resources
bus, dbus = EventBus(), DEventBus()

# Bridge
await bus.forward(dbus.ip, dbus.port)
```

## Distributed to Local

In the other hand, the distributed bus (server) can forward the messages that it receives to the local event bus.

```python
# Create resources
bus, dbus = EventBus(), DEventBus()

# Bridge
await dbus.forward(bus)
```
