import logging
import platform
from dataclasses import dataclass
from typing import List

import pytest
from dataclasses_json import DataClassJsonMixin

from aiodistbus import DEntryPoint, DEventBus, EntryPoint, Event, EventBus

logger = logging.getLogger("aiodistbus")
current_platform = platform.system()

linux_run_only = pytest.mark.skipif(
    current_platform != "Linux", reason="Test only can run on Linux"
)


@dataclass
class ExampleEvent(DataClassJsonMixin):
    msg: str


async def func(event: ExampleEvent):
    assert isinstance(event, ExampleEvent)
    logger.info(f"Received event {event}")


async def func_str(event: str):
    assert isinstance(event, str)
    logger.info(f"Received event {event}")


async def func_bytes(event: bytes):
    assert isinstance(event, bytes)
    logger.info("Received event %s", event)


async def func_int(event: int):
    assert isinstance(event, int)
    logger.info(f"Received event {event}")


async def func_float(event: float):
    assert isinstance(event, float)
    logger.info(f"Received event {event}")


async def func_bool(event: bool):
    assert isinstance(event, bool)
    logger.info(f"Received event {event}")


async def func_none():
    logger.info("Received event for None")


async def func_dict(event: dict):
    assert isinstance(event, dict)
    logger.info(f"Received event {event}")


async def func_list(event: List[str]):
    assert isinstance(event, List)
    logger.info(f"Received event {event}")


async def wildcard_func(event: Event):
    assert isinstance(event, Event)
    logger.info(f"Received event {event}")


@pytest.fixture
async def bus():
    bus = EventBus()
    yield bus
    await bus.close()


@pytest.fixture()
async def dbus():
    bus = DEventBus(ip="127.0.0.1")
    yield bus
    await bus.close()


@pytest.fixture
async def entrypoints():
    e1 = EntryPoint()
    e2 = EntryPoint()
    yield e1, e2
    await e1.close()
    await e2.close()


@pytest.fixture
async def dentrypoints():
    e1 = DEntryPoint()
    e2 = DEntryPoint()
    yield e1, e2
    await e1.close()
    await e2.close()
