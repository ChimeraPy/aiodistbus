import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional, Type

from dataclasses_json import DataClassJsonMixin


@dataclass
class Event(DataClassJsonMixin):
    type: str
    data: Optional[Any] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Handler:
    event_type: str
    function: Callable
    dtype: Optional[Type] = None


@dataclass
class Subscriptions:
    entrypoint_id: str
    handler: Handler
