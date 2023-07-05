from typing import Protocol
from abc    import abstractmethod


class ConnectorTemplate(Protocol):
    @abstractmethod
    def read_item(self, item_id: str):
        raise NotImplementedError

    @abstractmethod
    def save_item(self, item_id: str, dump):
        raise NotImplementedError

    @abstractmethod
    def remove_item(self, item_id: str):
        raise NotImplementedError