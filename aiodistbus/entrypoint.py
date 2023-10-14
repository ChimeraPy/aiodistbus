import abc
from collections import deque
from typing import Union, Callable, Coroutine, Type, TypeVar, Any, Optional, Literal, Dict

from .eventbus import EventBus
from .protocols import Event, OnHandler

T = TypeVar("T")

class AEntryPoint(abc.ABC):
    
    def __init__(self, id: str):

        # Parameters
        self.id = id

        # State information
        self._handlers: Dict[str, OnHandler]
        self._received: deque[str] = deque(maxlen=10)
   
    @abc.abstractmethod
    async def on(self, event_type: str, handler: Union[Callable, Coroutine], dataclass: Type["T"]):
        ...

    @abs.abstractmethod
    async def connect(self):
        ...

    @abc.abstractmethod
    async def emit(self, event_type: str, data: Any) -> Event:
        ...

    @abc.abstractmethod
    async def close(self):
        ...


class DEntryPoint(AEntryPoint):
    ...


class EntryPoint(AEntryPoint):
    
    async def connect(self):
        ...
