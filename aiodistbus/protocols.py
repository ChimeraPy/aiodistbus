import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Union, Callable, Coroutine, Type, Optional, Any

@dataclass
class Event:
    type: str
    data: Optional[Any] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

@dataclass
class OnHandler:
    event_type: str
    handler: Union[Callable, Coroutine]
    dataclass: Type["T"]
