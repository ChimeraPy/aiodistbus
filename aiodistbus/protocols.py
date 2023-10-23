import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Coroutine, Dict, Optional, Type, Union

from dataclasses_json import DataClassJsonMixin


@dataclass
class Event(DataClassJsonMixin):
    type: str
    data: Optional[Any] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class OnHandler:
    event_type: str
    handler: Union[Callable]
    dtype: Optional[Type] = None


@dataclass
class Subscriptions:
    entrypoint_id: str
    handler: OnHandler
