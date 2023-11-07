import pathlib
from dataclasses import dataclass
from typing import Optional

import pytest
from dataclasses_json import DataClassJsonMixin

from aiodistbus.protocols import Event
from aiodistbus.utils import encode, reconstruct

from .conftest import ExampleEvent


@dataclass
class ExampleEventWithPathlib(DataClassJsonMixin):
    path: Optional[pathlib.Path]


async def test_encode_dataclass_with_pathlib():
    data = ExampleEventWithPathlib(pathlib.Path("."))
    assert data.to_json()


@pytest.mark.parametrize(
    "data", [ExampleEvent("Hello"), ExampleEventWithPathlib(pathlib.Path("."))]
)
async def test_encode_decode(data):

    # Encode data
    encoded_data = encode(data)

    # Obtain the dtype and format it
    dtype = type(data)
    dtype_str = f"{dtype.__module__}.{dtype.__name__}"

    event = Event("test", encoded_data, dtype=dtype_str, id="")
    ser_event = event.to_json().encode()

    decoded_event = ser_event.decode()
    deser_event = await reconstruct(decoded_event)

    assert deser_event.data == data
