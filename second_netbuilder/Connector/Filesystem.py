from   Connector.ConnectorTemplate import ConnectorTemplate
from   Utility.Utility             import configuration_extraction
from   pathlib                     import Path
import os
import json


class Filesystem(ConnectorTemplate):
    def __init__(self):
        self.path = configuration_extraction("filesystem.json")["dumps_path"]
        Path(self.path).mkdir(parents=True, exist_ok=True)

    def read_item(self, item_id: str):
        try:
            fn = self.get_filepath(item_id)
            if not os.path.exists(fn): return None
            with open(fn) as f: return json.load(f)
        except Exception as e:
            print(e)
            return None

    def save_item(self, item_id: str, dump):
        try:
            fn = self.get_filepath(item_id)
            with open(fn, "w+") as f:
                json.dump(dump, f)
        except Exception as e:
            print(e)

    def remove_item(self, item_id: str):
        try:
            fn = self.get_filepath(item_id)
            if not os.path.exists(fn): return None
            os.remove(fn)
        except Exception as e:
            print(e)

    def get_filepath(self, item_id: str):
        return os.path.join(self.path, item_id + ".json")

