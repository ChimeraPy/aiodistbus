import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from collections import deque
from typing import Any, Callable, Coroutine, Dict, List, Optional, Type

from ..protocols import Event, OnHandler

logger = logging.getLogger("aiodistbus")


class AEntryPoint(ABC):
    def __init__(self):

        # State information
        self.id = str(uuid.uuid4())
        self._handlers: Dict[str, OnHandler] = {}
        self._wildcards: Dict[str, OnHandler] = {}
        self._received: deque[str] = deque(maxlen=10)
        self._tasks: List[asyncio.Task] = []

    def _wrapper(
        self, handler: Callable, unpack: bool = True, create_task: bool = False
    ) -> Callable:
        async def awrapper(event: Event):
            coro: Optional[Coroutine] = None
            if unpack:
                if (
                    type(event.data) is not type(None)
                    and self._handlers[event.type].dtype
                ):
                    coro = handler(event.data)
                else:
                    coro = handler()
            else:
                coro = handler(event)

            if coro:
                if create_task:
                    self._tasks.append(asyncio.create_task(coro))
                else:
                    await coro

            self._received.append(event.id)

        def wrapper(event: Event):
            if unpack:
                handler(event.data)
            else:
                handler(event)
            self._received.append(event.id)

        if asyncio.iscoroutinefunction(handler):
            return awrapper
        else:
            return wrapper

    @abstractmethod
    async def on(self, event_type: str, handler: Callable, dtype: Type):
        ...

    @abstractmethod
    async def connect(self):
        ...

    @abstractmethod
    async def emit(self, event_type: str, data: Any) -> Event:
        ...

    @abstractmethod
    async def close(self):
        ...
