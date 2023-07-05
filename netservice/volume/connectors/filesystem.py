import json
import os

from connectors.proto import ProtoConnector


class FSConnector(ProtoConnector):
    def __init__(self):
        with open("files/config.json", "r") as conf_file:
            self.path = json.load(conf_file)["fs_config"]["dumps_path"]

    def read_item(self, item_id: str):
        try:
            fn = self.get_filepath(item_id)
            if os.path.exists(fn):
                with open(fn) as f:
                    return json.load(f)
            return None
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

    def get_filepath(self, item_id: str):
        return self.path + item_id + ".json"
