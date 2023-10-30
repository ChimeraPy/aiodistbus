from ._log import setup as setup_log
from ._loop import setup as setup_loop
from .cfg import global_config
from .entrypoint import DEntryPoint, EntryPoint
from .eventbus import DEventBus, EventBus
from .protocols import Event
from .registry import registry
from .wrapper import DataClassEvent, make_evented

setup_log()
setup_loop()

__all__ = [
    "Event",
    "EventBus",
    "DEventBus",
    "EntryPoint",
    "DEntryPoint",
    "registry",
    "global_config",
    "make_evented",
    "DataClassEvent",
]
