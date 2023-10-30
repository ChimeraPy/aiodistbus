import asyncio
from asyncio import Task
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, Optional, TypeVar

# from .eventbus import Event, EventBus
from .eventbus import EventBus
from .observables import ObservableDict, ObservableList
from .protocols import Event

T = TypeVar("T")


@dataclass
class DataClassEvent:
    dataclass: Any


def make_evented(
    instance: T,
    bus: EventBus,
    event_name: Optional[str] = None,
    object: Optional[Any] = None,
    debounce_interval: float = 0.1,
) -> T:
    setattr(instance, "bus", bus)
    instance.__evented_values = {}  # type: ignore[attr-defined]

    # Name of the event
    if not event_name:
        event_name = f"{instance.__class__.__name__}.changed"

    # Dynamically create a new class with the same name as the instance's class
    new_class_name = instance.__class__.__name__
    NewClass = type(new_class_name, (instance.__class__,), {})

    async def emit_event(event: Event):
        await asyncio.sleep(debounce_interval)
        await bus._emit(event)

    def debounce_emit(event: Event):

        if hasattr(instance, "_debounce_task"):
            # If a task already exists, cancel it
            task: Task = getattr(instance, "_debounce_task")
            task.cancel()

        # Schedule a new delayed task to emit the event after debounce interval
        setattr(instance, "_debounce_task", asyncio.create_task(emit_event(event)))

    def make_property(name: str):
        def getter(self):
            return self.__evented_values.get(name)

        def setter(self, value):
            self.__evented_values[name] = value
            if object:
                event_data = object
            else:
                event_data = self

            event = Event(str(event_name), event_data)
            debounce_emit(event)

        return property(getter, setter)

    def callback(key, value):
        if object:
            event_data = object
        else:
            event_data = instance

        event = Event(str(event_name), event_data)
        debounce_emit(event)

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
            setattr(NewClass, f.name, make_property(f.name))

    # Change the class of the instance
    instance.__class__ = NewClass

    return instance
