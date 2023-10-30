from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Type

from .protocols import Handler
from .singleton import Singleton


@dataclass
class Namespace:
    handlers: Dict[str, Handler] = field(default_factory=dict)


class Registry(Singleton):
    """Registry for handlers"""

    def __init__(self):
        self.namespaces: Dict[str, Namespace] = {}

    def on(
        self, event: str, dtype: Optional[Type] = None, namespace: str = "default"
    ) -> Callable:
        """Decorator to register a handler

        Args:
            event (str): Event type
            dtype (Optional[Type], optional): Data type. Defaults to None.
            namespace (str, optional): Namespace. Defaults to "default".

        Returns:
            Callable: Decorator

        Examples:
            >>> from aiodistbus import registry
            >>> @registry.on("test")
            ... def test_handler(event):
            ...     print(event)
            ...
            >>> registry.get_handlers()
            {'test': Handler(event_type='test', function=<function test_handler at 0x7f8b1c0b9d30>, dtype=None)}

        """
        # Store the handler information
        if namespace not in self.namespaces:
            self.namespaces[namespace] = Namespace()

        def decorator(func: Callable):
            # Add handler
            handler = Handler(event, func, dtype)  # <-- Missing func
            self.namespaces[namespace].handlers[event] = handler
            return func

        return decorator

    def get_handlers(self, namespace: str = "default") -> Dict[str, Handler]:
        """Get handlers for namespace

        Args:
            namespace (str, optional): Namespace. Defaults to "default".

        Returns:
            Dict[str, Handler]: Handlers

        """
        return self.namespaces[namespace].handlers


registry = Registry()
