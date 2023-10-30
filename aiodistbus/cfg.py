import json
from typing import Callable, Dict, List, Optional, Type, TypeVar, Union

T = TypeVar("T")

########################################################################
## Serialization Configuration
########################################################################

Json = Union[dict, Dict, list, List, str, int, float, bool, None]

SFunction = Callable[[Type[T]], bytes]
DFunction = Callable[[bytes], T]


class _GlobalConfig:
    """Global configuration for serialization and deserialization

    Examples:
        >>> from aiodistbus import cfg
        >>> cfg.global_config.encoders[pathlib.Path] = lambda x: str(x).encode()
        >>> cfg.global_config.decoders[pathlib.Path] = lambda x: pathlib.Path(x.decode())

    """

    def __init__(self):
        self.encoders: Dict[Union[Type, Optional[Type]], SFunction[Type]] = {
            str: lambda x: x.encode("utf-8"),
            bytes: lambda x: x,
            Json: lambda x: json.dumps(x).encode("utf-8"),
        }
        self.decoders: Dict[Union[Type, Optional[Type]], DFunction[Type]] = {
            str: lambda x: x.decode(),
            bytes: lambda x: x,
            Json: lambda x: json.loads(x.decode()),
        }

    def get_encoder(self, dtype: Union[Type, Optional[Type]]) -> SFunction[Type]:
        """Get encoder for type

        Args:
            dtype (Union[Type, Optional[Type]]): Type to encode

        Raises:
            ValueError: If encoder not found

        Returns:
            SFunction[Type]: Encoder function

        """
        if dtype in Json.__args__:  # type: ignore
            return self.encoders[Json]  # type: ignore
        elif dtype in self.encoders:
            return self.encoders[dtype]
        else:
            raise ValueError(f"Encoder not found for {dtype}")

    def get_decoder(self, dtype: Union[Type, Optional[Type]]) -> DFunction[Type]:
        """Get decoder for type

        Args:
            dtype (Union[Type, Optional[Type]]): Type to decode

        Raises:
            ValueError: If decoder not found

        Returns:
            DFunction[Type]: Decoder function

        """
        if dtype in Json.__args__:  # type: ignore
            return self.decoders[Json]  # type: ignore
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
