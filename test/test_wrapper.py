import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List

import pytest
from dataclasses_json import DataClassJsonMixin

from aiodistbus import make_evented

logger = logging.getLogger("aiodistbus")


@dataclass
class SomeClass(DataClassJsonMixin):
    number: int
    string: str


@dataclass
class HelloEventData:
    message: str


@dataclass
class NestedClass(DataClassJsonMixin):
    number: int
    subclass: HelloEventData
    map: Dict[str, str]
    vector: List[str]


async def someclass_handler(data: SomeClass):
    logger.debug(f"Got someclass event: {data}")
    assert isinstance(data, SomeClass)


async def nestedclass_handler(data: NestedClass):
    logger.debug(f"Got nestedclass event: {data}")
    assert isinstance(data, NestedClass)


async def test_make_evented(bus, entrypoints):

    # Create resources
    e1, _ = entrypoints
    await e1.connect(bus)
    await e1.on("SomeClass.changed", someclass_handler, SomeClass)

    # Create the evented class
    data = make_evented(SomeClass(number=1, string="hello"), bus=bus)

    # Trigger an event by changing the class
    data.number = 2
    await asyncio.sleep(1)
    assert len(e1._received) > 0


@pytest.mark.parametrize(
    "cls, kwargs",
    [
        (SomeClass, {"number": 1, "string": "hello"}),
    ],
)
def test_evented_to_json(cls, kwargs, bus):
    # Create the evented class
    data = make_evented(cls(**kwargs), bus=bus)
    data.to_json()


def test_make_evented_multiple(bus):
    # Create the evented class
    make_evented(SomeClass(number=1, string="hello"), bus=bus)
    make_evented(SomeClass(number=1, string="hello"), bus=bus)
    make_evented(SomeClass(number=1, string="hello"), bus=bus)


async def test_make_evented_nested(bus, entrypoints):

    # Create resources
    e1, _ = entrypoints
    await e1.connect(bus)
    await e1.on("NestedClass.changed", nestedclass_handler, SomeClass)

    data_class = NestedClass(
        number=1,
        subclass=HelloEventData(message="hello"),
        map={"test": "test"},
        vector=["hello", "there"],
    )
    nested_data = make_evented(
        data_class,
        bus=bus,
    )

    logger.debug(data_class)

    nested_data.number = 5
    await asyncio.sleep(1)
    a = len(e1._received)
    assert a > 0

    nested_data.map["new"] = "key"
    await asyncio.sleep(1)
    b = len(e1._received)
    assert b > a

    nested_data.subclass.message = "goodbye"
    await asyncio.sleep(1)
    c = len(e1._received)
    assert c > b

    nested_data.vector.append("this")
    await asyncio.sleep(1)
    d = len(e1._received)
    assert d > c

    # Then it must also be jsonable
    logger.debug(nested_data.to_json())
