import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from collections import deque
from typing import Any, Callable, Coroutine, Dict, List, Optional, Type

from ..protocols import Event, Handler
from ..registry import Registry
from ..utils import safe_coro

logger = logging.getLogger("aiodistbus")


class AEntryPoint(ABC):
    def __init__(self):
        """Abstract entrypoint for eventbus"""

        # State information
        self.id = str(uuid.uuid4())
        self._handlers: Dict[str, Handler] = {}
        self._wildcards: Dict[str, Handler] = {}
        self._received: deque[str] = deque(maxlen=1000)
        self._tasks: List[asyncio.Task] = []

    def _wrapper(
        self, func: Callable, unpack: bool = True, create_task: bool = False
    ) -> Callable:
        """Wrapper for handlers

        The wrapper provides an approach for logging which events have been transmitted

        Args:
            func (Callable): Function to wrap
            unpack (bool, optional): Unpack the event. Defaults to True.
            create_task (bool, optional): Create a task for the handler. Defaults to False.

        Returns:
            Callable: Wrapped function

        """
        # Wrapper for async functions
        async def awrapper(event: Event):
            coro: Optional[Coroutine] = None
            if unpack:
                if (
                    type(event.data) is not type(None)
                    and self._handlers[event.type].dtype
                ):
                    coro = func(event.data)
                else:
                    coro = func()
            else:
                coro = func(event)

            if coro:
                # Create safe coro with error msg
                scoro = safe_coro(
                    coro, f"Error in (type: {event.type}, handler {func.__name__})"
                )
                if create_task:
                    self._tasks.append(asyncio.create_task(scoro))
                else:
                    await scoro

            self._received.append(event.id)

        # Wrapper for sync functions
        async def wrapper(event: Event):

            try:
                if unpack:
                    func(event.data)
                else:
                    func(event)
            except Exception as e:
                logger.error(
                    f"Error in handler (type: {event.type}, handler {func.__name__}): {e}"
                )

            self._received.append(event.id)

        # Select according to function type
        if asyncio.iscoroutinefunction(func):
            return awrapper
        else:
            return wrapper

    @abstractmethod
    async def _update_handlers(
        self, event_type: Optional[str] = None, remove: bool = False
    ):
        ...

    ####################################################################
    ## Public API
    ####################################################################

    async def use(self, registry: Registry, namespace: str = "default"):
        """Use a registry

        Args:
            registry (Registry): Registry to use
            namespace (str, optional): Namespace. Defaults to "default".

        """
        # Obtain the handlers
        for event_type, handler in registry.get_handlers(namespace).items():
            await self.on(event_type, handler.function, handler.dtype)

    async def on(
        self,
        event_type: str,
        func: Callable,
        dtype: Optional[Type] = None,
        create_task: bool = False,
    ):
        """Register a handler

        Args:
            event_type (str): Event type
            func (Callable): Function to call
            dtype (Optional[Type], optional): Data type. Defaults to None.
            create_task (bool, optional): Create a task for the handler. Defaults to False.

        Examples:
            >>> from aiodistbus import AEntryPoint
            >>> ep = AEntryPoint()
            >>> async def test_handler():
            ...     print("Hello World")
            ...
            >>> await ep.on("test", test_handler)

        """
        # Track handlers (supporting wildcards)
        if "*" not in event_type:
            wrapped_func = self._wrapper(func, create_task=create_task)
            handler = Handler(event_type, wrapped_func, dtype)
            self._handlers[event_type] = handler
        else:
            wrapped_func = self._wrapper(func, unpack=False, create_task=create_task)
            handler = Handler(event_type, wrapped_func, dtype)
            self._wildcards[event_type] = handler

        await self._update_handlers(event_type)

    async def off(self, event_type: str):
        """Remove a handler

        Args:
            event_type (str): Event type

        """
        # Track handlers (supporting wildcards)
        if "*" not in event_type:
            del self._handlers[event_type]
        else:
            del self._wildcards[event_type]

        await self._update_handlers(event_type, remove=True)

    @abstractmethod
    async def emit(
        self, event_type: str, data: Any, id: Optional[str] = None
    ) -> Optional[Event]:
        """Emit an event

        Args:
            event_type (str): Event type
            data (Any): Data to send
            id (Optional[str], optional): Event ID. Defaults to None.

        Returns:
            Optional[Event]: Event object

        """
        ...

    @abstractmethod
    async def close(self):
        """Close the entrypoint"""
        ...
