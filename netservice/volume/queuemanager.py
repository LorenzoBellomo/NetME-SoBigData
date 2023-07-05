import asyncio
import json
import base64
import jsons
from   connectors.filesystem import FSConnector
from   utils import Utils
import logging
from   worker_new import make_net


logging.basicConfig(filename="files/netme.log", level=logging.DEBUG)


class QueueManager:
    mongo_db   = None

    def __init__(self):
        self.dumps_connector  = FSConnector()
        self.mongo_db         = Utils.mongo_db()

    ##############################################################################################
    # CONSOLE QUEUE #
    ##############################################################################################
    def create_console_queue(self, req: dict):
        item_id = req["id"]
        try:
            self.mongo_db["requests"].insert_one({"_id": item_id, "status": "PROGRESS", "logs": []})
        except Exception as e:
            logging.error("QUEUEMANAGER create_console_queue: " + str(e))
        producer = asyncio.create_task(self.console_producer_redis(req))
        asyncio.create_task(self.wait_console_queue(item_id, producer))

    async def wait_console_queue(self, item_id: str, producer):
        await asyncio.gather(producer)
        # try:
        #     self.mongo_db["requests"].update_one(
        #         {"_id": item_id}, {"$set": {"status": "COMPLETED"}}
        #     )
        # except Exception as e:
        #     logging.error("QUEUEMANAGER wait_console_queue: " + str(e))

    # TASK CELERY CREATION
    def create_celery_task(self, req, max_tries: int, current: int = 0):
        current  += 1
        task      = None
        try: task = make_net.delay(req)
        except Exception as e:
            print(f"[TRY {current}] error for request:", req["id"], e)
            logging.error(f"[TRY {current}] ERROR FOR REQ: " + req["id"] + " " + str(e))
        if task is None and current < max_tries:
            task = self.create_celery_task(req, max_tries, current)
        return task

    async def console_producer_redis(self, req: dict):
        try:
            # CREATE CELERY TASK
            task = self.create_celery_task(req, max_tries=3)
            while not task.ready():
                await asyncio.sleep(1)
            # RESULTS
            net = task.result
            if net is not None:
                net["search_data"] = Utils.create_search_data(req)
                try:
                    self.mongo_db["requests"].update_one(
                        {"_id": req["id"]}, {"$set": {"status": "COMPLETED"}}
                    )
                except Exception as e:
                    logging.error("QUEUEMANAGER wait_console_queue: " + str(e))
                self.dumps_connector.save_item(req["id"], net)
            else:
                self.mongo_db["requests"].update_one({"_id": req["id"]}, {"$set": {"status": "ERROR"}})
        except Exception as e:
            print("error for request:", req["id"], e)
            logging.error("ERROR FOR REQUEST: " + req["id"])
            self.mongo_db["requests"].update_one({"_id": req["id"]}, {"$set": {"status": "ERROR"}})

    ##############################################################################################
    # ENTRY POINTS #
    ##############################################################################################
    async def new_request(self, _req, id_: str):
        req = jsons.dump(_req.__dict__)
        if _req.queryMode == "pdf":
            fn_list = []
            files = json.loads(_req.input)
            for f in files:
                fn = f'files/pdf/{id_}_{f["fname"]}'
                with open(fn, "wb") as fw:
                    fn_list.append(fn)
                    fw.write(base64.b64decode(f["data"].split(",")[1:2][0]))
            del req["input"]            # only for files
            req["fn_list"] = fn_list    # add file names
        req["id"] = id_
        self.create_console_queue(req)  # like a producer

    def read_item(self, item_id):
        try:
            req = self.mongo_db["requests"].find_one({"_id": item_id})
            if req is not None and req["status"] == "PROGRESS":
                return {"status": 200, "console_token": item_id, "logs": req["logs"]}
            elif req is not None and req["status"] == "ERROR":
                return {"status": 500, "console_token": item_id, "logs": req["logs"]}
            else:
                dump = self.dumps_connector.read_item(item_id)
                if dump is None:
                    return {"status": 404}
                else:
                    return {"status": 200, "result": dump}
        except Exception as e:
            logging.error("QUEUEMANAGER read_item: " + str(e))
            return {}
