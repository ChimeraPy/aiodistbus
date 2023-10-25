import logging
from typing import Any, Iterable, List, Optional, Type

from dataclasses_json import DataClassJsonMixin

from .cfg import EVENT_BLACKLIST, global_config
from .protocols import Event

logger = logging.getLogger("aiodistbus")

#############################################################################
## Wildcard Handling
#############################################################################


def wildcard_filtering(topic: str, wildcard: str) -> bool:

    for i, j in zip(topic.split("."), wildcard.split(".")):
        if j == "*":
            return True
        if i != j:
            return False

    return False


def wildcard_search(topic: str, wildcards: Iterable[str]) -> List[str]:
    if topic in EVENT_BLACKLIST:
        return []
    return [w for w in wildcards if wildcard_filtering(topic, w)]


#############################################################################
## Decoding
#############################################################################


def decode(event_str: str) -> Event:
    event = Event.from_json(event_str)
    if isinstance(event.data, list):
        event.data = bytes(event.data)
    return event


def reconstruct_event_data(event: Event, dtype: Type) -> Event:

    if hasattr(dtype, "__annotations__"):
        decoder = lambda x: dtype.from_json(bytes(x).decode())
    else:
        try:
            decoder = global_config.get_decoder(dtype)
        except ValueError:
            logger.error(f"Could not find decoder for {dtype}")

    event.data = decoder(event.data)

    return event


async def reconstruct(event_str: str, dtype: Optional[Type] = None) -> Event:
    event = decode(event_str)  # str -> Event
    if dtype:
        event = reconstruct_event_data(event, dtype)
    return event


#############################################################################
## Encoding
#############################################################################


def encode(data: Any) -> bytes:
    # Serialize the data
    if isinstance(data, DataClassJsonMixin):
        encoder = lambda x: x.to_json().encode("utf-8")
    else:
        encoder = global_config.get_encoder(type(data))

    # Encode the data
    return encoder(data)
