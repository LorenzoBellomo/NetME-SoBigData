from typing import Protocol
from abc import abstractmethod


class ProtoConnector(Protocol):
    @abstractmethod
    def read_item(self, item_id: str):
        raise NotImplementedError

    @abstractmethod
    def save_item(self, item_id: str, dump):
        raise NotImplementedError
