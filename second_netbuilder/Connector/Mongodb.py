from   Connector.ConnectorTemplate import ConnectorTemplate
from   Utility.Utility             import Utility
from   bson                        import ObjectId


class MongoDBConnector(ConnectorTemplate):
    def __init__(self):
        self.mongo_db = Utility.mongo_db()

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

    def remove_item(self, item_id: str):
        try:
            self.mongo_db["dumps"].delete_one({"_id": item_id})
        except Exception as e:
            print(str(e))
