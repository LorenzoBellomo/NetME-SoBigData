import json
import logging
import aioredis
from   typing                  import Optional
from   fastapi                 import FastAPI, WebSocket
from   starlette.requests      import Request
from   pydantic                import BaseModel
from   fastapi.middleware.cors import CORSMiddleware
from   slowapi                 import Limiter, _rate_limit_exceeded_handler
from   slowapi.util            import get_remote_address
from   slowapi.errors          import RateLimitExceeded
from   connectionmanager       import ConnectionManager
from   utils                   import Utils
from   queuemanager            import QueueManager


class RequestData(BaseModel):
    searchOn    : str
    searchType  : str
    papersNumber: str
    sortType    : str
    queryMode   : str
    input       : str
    networkName : str

logging.basicConfig(filename="files/netme.log", level=logging.DEBUG)

##############################################################################################
# MAIN #
##############################################################################################
limiter           = Limiter(key_func=get_remote_address)
app               = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
origins           = ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


queue_manager      = QueueManager()
##############################################################################################
# MAIN #
##############################################################################################


@app.get("/test")
@limiter.limit("100/minute")
async def homepage(request: Request):
    return {"Hello": "World"}


@app.post("/send_data")
@limiter.limit("600/minute")
async def send_data(req: RequestData, request: Request):
    # TODO: validate requestData
    id = Utils.get_timestamp_id()
    await queue_manager.new_request(req, id)
    print(id)
    return {"query_id": id}


@app.get("/items/{item_id}")
@limiter.limit("1200/minute")
def read_item(item_id: str, request: Request, q: Optional[str] = None):
    data = queue_manager.read_item(item_id)
    return data


@app.websocket("/ws/{item_id}")
async def websocket_endpoint(websocket: WebSocket, item_id: str):
    mongo_db = Utils.mongo_db()
    await websocket.accept()
    redis  = aioredis.Redis.from_url("redis://" + Utils.rabbit_url + ":6379/0", decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.subscribe(item_id)
    while True:
        message = await pubsub.get_message()
        if message is not None and type(message["data"]) != int:
            data = json.loads(message["data"])
            message = f"{data['time']} {data['msg']}||{data['progress']:.2f}"
            item_id = data["routing_key"]
            await websocket.send_text(message)
            try:
                mongo_db["requests"].update_one({"_id": item_id}, {"$push": {"logs": message}, "$set": {"status": data['status']}})
                if data['progress'] >= 1.0 or data['status'] != "PROGRESS": break
            except Exception as e:
                logging.error(str(e))
                break
    await pubsub.unsubscribe(item_id)
    pubsub.close()
