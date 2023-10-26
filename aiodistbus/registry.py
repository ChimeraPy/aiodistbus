from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Type

from .protocols import Handler
from .singleton import Singleton


@dataclass
class Namespace:
    handlers: Dict[str, Handler] = field(default_factory=dict)


class Registry(Singleton):
    def __init__(self):
        self.namespaces: Dict[str, Namespace] = {}

    def on(
        self, event: str, dtype: Optional[Type] = None, namespace: str = "default"
    ) -> Callable:

        # Store the handler information
        if namespace not in self.namespaces:
            self.namespaces[namespace] = Namespace()

        def decorator(func: Callable):
            # Add handler
            handler = Handler(event, func, dtype)  # <-- Missing func
            self.namespaces[namespace].handlers[event] = handler
            return func

        return decorator

    def get_handlers(self, namespace: str = "default"):
        return self.namespaces[namespace].handlers


registry = Registry()
