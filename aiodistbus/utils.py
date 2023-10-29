import logging
import zlib
from typing import Any, Coroutine, Iterable, List, Optional, Type

from dataclasses_json import DataClassJsonMixin

from .cfg import EVENT_BLACKLIST, global_config
from .protocols import Event

logger = logging.getLogger("aiodistbus")

#############################################################################
## Wildcard Handling
#############################################################################


def wildcard_filtering(topic: str, wildcard: str) -> bool:
    """Filter a topic against a wildcard

    Args:
        topic (str): Topic to filter
        wildcard (str): Wildcard to filter against

    Returns:
        bool: True if topic matches wildcard

    """
    for i, j in zip(topic.split("."), wildcard.split(".")):
        if j == "*":
            return True
        if i != j:
            return False

    return False


def wildcard_search(topic: str, wildcards: Iterable[str]) -> List[str]:
    """Search for matching wildcards

    Args:
        topic (str): Topic to search
        wildcards (Iterable[str]): Wildcards to search

    Returns:
        List[str]: List of matching wildcards

    """
    if topic in EVENT_BLACKLIST:
        return []
    return [w for w in wildcards if wildcard_filtering(topic, w)]


#############################################################################
## Error Handling
#############################################################################


async def safe_coro(coro: Coroutine, error_msg: Optional[str] = None):
    """Safely run a coroutine, logging any errors

    Args:
        coro (Coroutine): Coroutine to run
        error_msg (Optional[str], optional): Error message to log. Defaults to None.

    """
    try:
        await coro
    except Exception as e:
        if error_msg:
            logger.error(f"aiodistbus: {error_msg}: {e}")
        else:
            logger.error(f"aiodistbus: Error in coroutine {coro}: {e}")


#############################################################################
## Decoding
#############################################################################


def decode(event_str: str) -> Event:
    """Decode an event from a string

    Args:
        event_str (str): Event string

    Returns:
        Event: Event object

    """
    event = Event.from_json(event_str)
    if isinstance(event.data, list):
        event.data = bytes(event.data)
    return event


def reconstruct_event_data(event: Event, dtype: Type) -> Event:
    """Reconstruct the data of an event

    Args:
        event (Event): Event to reconstruct
        dtype (Type): Type to reconstruct to

    Returns:
        Event: Reconstructed event

    """
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
    """Reconstruct an event from a string

    Args:
        event_str (str): Event string
        dtype (Optional[Type], optional): Type to reconstruct to. Defaults to None.

    Returns:
        Event: Reconstructed event

    """
    event = decode(event_str)  # str -> Event
    if dtype:
        event = reconstruct_event_data(event, dtype)
    return event


#############################################################################
## Encoding
#############################################################################


def encode(data: Any) -> bytes:
    """Encode data to bytes

    Args:
        data (Any): Data to encode

    Returns:
        bytes: Encoded data

    """
    # Serialize the data
    if isinstance(data, DataClassJsonMixin):
        encoder = lambda x: x.to_json().encode("utf-8")
    else:
        encoder = global_config.get_encoder(type(data))

    # Encode the data
    return encoder(data)


#############################################################################
## Checksum
#############################################################################


def verify_checksum(data: bytes, checksum: bytes) -> bool:
    """Verify the checksum of data

    Args:
        data (bytes): Data to verify
        checksum (bytes): Checksum to verify against

    Returns:
        bool: True if checksum is correct

    """
    return zlib.crc32(data) == int.from_bytes(checksum, "big")
