from connectors.proto import ProtoConnector
from utils import Utils


class MongoDBConnector(ProtoConnector):
    def __init__(self):
        self.mongo_db = Utils.mongo_db()

    def read_item(self, item_id):
        try:
            dump = self.mongo_db["dumps"].find_one({"_id": item_id})
            return dump
        except Exception as e:
            print(e)
            return None

    def save_item(self, item_id, dump):
        try:
            self.mongo_db["dumps"].update_one(
                {"_id": item_id}, {"$set": dump}, upsert=True
            )
        except Exception as e:
            print(e)
