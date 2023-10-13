from dataclasses import dataclass
from typing import Dict, List, Literal, Type

from .protocols import Event, OnHandler
from .utils import get_ip_address

@dataclass
class Subscription:
    entrypoint: str
    mode: Literal['local', 'remote']
    event_type: str
    dataclass: Type["T"]


class EventBus():
    
    def __init__(self,  port: int = 0):

        # State information
        self._ip: str = get_ip_address()
        self._port: int = port
        self._routes: Dict[str, List[Subscription]] = {}

    async def aserve(self):
        ...

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port

    async def emit(self, event: Event):
        ...

    # def filter_handlers(self, event_type: str, handlers: Dict[str,OnHandler]) -> List[OnHandler]:
    #     filtered_handlers: List[OnHandler] = []

    #     topics = event_type.split("/")
    #     for handler in handlers.values():
    #         handler_topics = handler.event_type.split("/")

    #         # Support for wildcards (*)
    #         for topic, handler_topic in zip(topics, handler_topics):
    #             if handler_topic == "*":
    #                 filtered_handlers.append(handler)
    #                 break
    #             if handler_topic != topic:
    #                 break

    #     return filtered_handlers

    async def close(self):
        ...
