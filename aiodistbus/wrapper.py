import asyncio
from asyncio import Task
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, Callable, Optional, Type, TypeVar

# from .eventbus import Event, EventBus
from .eventbus import EventBus
from .observables import ObservableDict, ObservableList
from .protocols import Event

T = TypeVar("T")


@dataclass
class DataClassEvent:
    dataclass: Any


async def emit_event(bus: EventBus, event: Event, debounce_interval: float):
    await asyncio.sleep(debounce_interval)
    await bus._emit(event)


def debounce_emit(instance: Any, event: Event, bus: EventBus, debounce_interval: float):
    """Debounce emit

    Args:
        event (Event): Event to emit

    """
    if hasattr(instance, "_debounce_task"):
        # If a task already exists, cancel it
        task: Task = instance._debounce_task
        task.cancel()

    # Schedule a new delayed task to emit the event after debounce interval
    instance._debounce_task = asyncio.create_task(
        emit_event(bus, event, debounce_interval)
    )


def wrap_callback(
    cls: Type,
    instance: Any,
    bus: EventBus,
    event_name: str,
    callback: Callable,
    property_callback: Callable,
):
    for f in fields(instance.__class__):
        if f.name != "bus":
            attr_value = getattr(instance, f.name)

            # Check if other dataclass
            if is_dataclass(attr_value):
                attr_value = make_evented(attr_value, bus, event_name, instance)

            # If the attribute is a dictionary, replace it with an ObservableDict
            elif isinstance(attr_value, dict):
                attr_value = ObservableDict(attr_value)
                attr_value.set_callback(callback)

            # Handle list
            elif isinstance(attr_value, list):
                attr_value = ObservableList(attr_value)
                attr_value.set_callback(callback)

            instance.__evented_values[f.name] = attr_value  # type: ignore[attr-defined]
            setattr(cls, f.name, property_callback(f.name))


def make_evented(
    instance: T,
    bus: EventBus,
    event_name: Optional[str] = None,
    object: Optional[Any] = None,
    debounce_interval: float = 0.1,
) -> T:
    """Make a dataclass evented

    Args:
        instance (T): Instance of dataclass
        bus (EventBus): EventBus
        event_name (Optional[str], optional): Name of the event. Defaults to None.
        object (Optional[Any], optional): Object to send with event. Defaults to None.
        debounce_interval (float, optional): Debounce interval. Defaults to 0.1.

    Returns:
        T: Evented dataclass

    Examples:
        >>> from dataclasses import dataclass
        >>> from aiodistbus import EventBus, make_evented
        >>> bus = EventBus()
        >>> @dataclass
        ... class Test:
        ...     a: int = 0
        ...     b: int = 0
        ...
        >>> test = Test()
        >>> test = make_evented(test, bus)
        >>> test.a = 1 # Event emitted

    """
    instance.bus = bus  # type: ignore[attr-defined]
    instance.__evented_values = {}  # type: ignore[attr-defined]

    # Name of the event
    if not event_name:
        event_name = f"{instance.__class__.__name__}.changed"

    # Dynamically create a new class with the same name as the instance's class
    new_class_name = instance.__class__.__name__
    NewClass = type(new_class_name, (instance.__class__,), {})

    def make_property(name: str):
        """Make a property

        Args:
            name (str): Name of the property

        """

        def getter(self):
            return self.__evented_values.get(name)

        def setter(self, value):
            self.__evented_values[name] = value
            if object:
                event_data = object
            else:
                event_data = self

            event = Event(str(event_name), event_data)
            debounce_emit(instance, event, bus, debounce_interval)

        return property(getter, setter)

    def callback(key: str, value: Any):
        """Callback for ObservableDict and ObservableList"""
        if object:
            event_data = object
        else:
            event_data = instance

        event = Event(str(event_name), event_data)
        debounce_emit(instance, event, bus, debounce_interval)

    # Wrap the callback
    wrap_callback(NewClass, instance, bus, event_name, callback, make_property)

    # Change the class of the instance
    instance.__class__ = NewClass

    return instance
