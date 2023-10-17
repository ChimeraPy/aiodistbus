import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Union

from dataclasses_json import DataClassJsonMixin

# Constants
MSG_TO_TYPE_MAP = {
    "SUBSCRIBE": "SubscribeData",
}

###########################################################################################
## Structure
###########################################################################################


@dataclass
class Data(DataClassJsonMixin):
    ...


@dataclass
class Message(DataClassJsonMixin):
    type: str
    data: Union[Data, Dict] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


###########################################################################################
## Messages
###########################################################################################


@dataclass
class SubscribeData(Data, DataClassJsonMixin):
    event_type: List[str]
