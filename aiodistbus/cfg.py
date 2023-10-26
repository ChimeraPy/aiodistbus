import json
from typing import Callable, Dict, List, Optional, Type, Union

########################################################################
## Serialization Configuration
########################################################################

Json = Union[dict, Dict, list, List, str, int, float, bool, None]


class _GlobalConfig:
    def __init__(self):
        self.encoders: Dict[Union[Type, Optional[Type]], Callable[Type, bytes]] = {
            str: lambda x: x.encode("utf-8"),
            bytes: lambda x: x,
            Json: lambda x: json.dumps(x).encode("utf-8"),
        }
        self.decoders: Dict[Union[Type, Optional[Type]], Callable] = {
            str: lambda x: x.decode(),
            bytes: lambda x: x,
            Json: lambda x: json.loads(x.decode()),
        }

    def get_encoder(self, dtype: Union[Type, Optional[Type]]) -> Callable:
        if dtype in Json.__args__:
            return self.encoders[Json]
        elif dtype in self.encoders:
            return self.encoders[dtype]
        else:
            raise ValueError(f"Encoder not found for {dtype}")

    def get_decoder(self, dtype: Union[Type, Optional[Type]]) -> Callable:
        if dtype in Json.__args__:
            return self.decoders[Json]
        elif dtype in self.decoders:
            return self.decoders[dtype]
        else:
            raise ValueError(f"Decoder not found for {dtype}")


global_config = _GlobalConfig()


########################################################################
## Event Blacklist
########################################################################

EVENT_BLACKLIST = [
    "aiodistbus.eventbus.close",
    "aiodistbus.eventbus.pulse",
]
