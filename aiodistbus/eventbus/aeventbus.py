import logging
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict

from ..protocols import Subscriptions

logger = logging.getLogger(__name__)


class AEventBus(ABC):
    """Abstract eventbus

    This class is the abstract base class for all eventbuses

    """

    def __init__(self):

        # State information
        self._running = False
        self._uuid = str(uuid.uuid4())
        self._subs: Dict[str, Dict[str, Subscriptions]] = defaultdict(dict)

    @property
    def running(self) -> bool:
        return self._running

    @property
    def uuid(self) -> str:
        return self._uuid

    @abstractmethod
    async def close(self):
        ...
