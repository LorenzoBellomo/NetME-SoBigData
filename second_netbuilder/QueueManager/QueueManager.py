import asyncio
import base64
import jsons
import json
from   Connector.Filesystem import Filesystem
from   Worker               import make_net
from   Utility.Utility      import Utility as Ut
from   pathlib              import Path


# GLOBAL VARIABLES
STS  = "status"
REQ  = "requests"
CTK  = "console_token"
LOG  = "logs"
RES  = "result"
ID   = "_id"
SDAT = "search_data"
SET  = "$set"


class QueueManager:
    def __init__(self):
        self.dumps_connector = Filesystem()
        self.utility         = Ut()
        self.mongo_db        = self.utility.mongo_db()
        self.saving_path     = "Files/Pdf"
        Path(self.saving_path).mkdir(parents=True, exist_ok=True)

    # TASK CELERY CREATION
    def create_celery_task(self, req, max_tries: int, current: int = 0):
        current  += 1
        task      = None
        try: task = make_net.delay(req)
        except Exception as e: print(str(e))
        if not (task is None and current < max_tries): return task
        self.create_celery_task(req, max_tries, current)

    def put_into_mongo(self, id_, message):
        self.mongo_db[REQ].update_one(
           {ID : id_}, {SET: {STS: message}}
        )

    # REDIS CONSOLE PRODUCER
    async def console_producer_redis(self, req: dict):
        try:
            # CELERY TASK CREATION
            task = self.create_celery_task(req, max_tries=3)
            if task is None:
                self.put_into_mongo(req["id"], "ERROR")
                return
            while not task.ready(): await asyncio.sleep(1)
            # RESULTS
            net  = task.result
            if net is not None:
                net["search_data"] = self.utility.create_search_data(req)
                try:
                    self.put_into_mongo(req["id"], "COMPLETED")
                except Exception as e: print(str(e))
                self.dumps_connector.save_item(req["id"], net)
            else: self.put_into_mongo(req["id"], "ERROR")
        except Exception as e:
            print(str(e))
            self.put_into_mongo(req["id"], "ERROR")

    # CONSOLE QUEUE WAITING
    @staticmethod
    async def wait_console_queue(producer):
        await asyncio.gather(producer)

    # CONSOLE CREATION
    def create_console_queue(self, req: dict):
        item_id = req["id"]
        try:
            self.mongo_db[REQ].insert_one(
                {
                    ID   : item_id,
                    STS  : "PROGRESS",
                    LOG  : []
                })
        except Exception as e:
            print("Error:", str(e))
        producer = asyncio.create_task(self.console_producer_redis(req))
        asyncio.create_task(self.wait_console_queue(producer))

    # MAIN PART (ENTRY POINT)
    # 1.
    # NEW REQUEST ELABORATION
    async def new_request(self, _req, id_: str):
        req = jsons.dump(_req.__dict__)
        if _req.queryMode == "pdf":
            fn_list = []
            files = json.loads(_req.input)
            for f in files:
                fn = self.saving_path + f'/{id_}_{f["fname"]}'
                with open(fn, "wb") as fw:
                    fn_list.append(fn)
                    fw.write(base64.b64decode(f["data"].split(",")[1:2][0]))
            del req["input"]  # only for files
            req["fn_list"] = fn_list
        req["id"] = id_
        self.create_console_queue(req)

    # 2.
    # ITEM READING
    def read_item(self, item_id):
        try:
            req = self.mongo_db[REQ].find_one({"_id": item_id})
            if req is not None and req[STS] == "PROGRESS":
                return {STS: 200, CTK: item_id, LOG: req[LOG]}
            elif req is not None and req[STS] == "ERROR":
                return {STS: 500, CTK: item_id, LOG: req[LOG]}
            else:
                dump = self.dumps_connector.read_item(item_id)
                if dump is None: return {STS: 404}
                else: return {STS: 200, RES: dump}
        except Exception as e:
            print(str(e))
            return {}

    def delete_item(self, item_id):
        self.mongo_db["dumps"].delete_one({"_id": item_id})
        self.mongo_db[REQ].delete_one({"_id": item_id})
        self.dumps_connector.remove_item(item_id)