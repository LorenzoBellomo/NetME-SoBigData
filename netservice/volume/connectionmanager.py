import asyncio
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections = dict()

    async def connect(self, item_id: str, websocket: WebSocket):
        await websocket.accept()
        if item_id not in self.active_connections:
            self.active_connections[item_id] = []
        self.active_connections[item_id].append(websocket)

    def disconnect(self, item_id: str, websocket: WebSocket):
        self.active_connections[item_id].remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def send_topic_message(self, item_id, message: str):
        if item_id in self.active_connections:
            for ws in self.active_connections[item_id]:
                try:
                    await asyncio.wait_for(ws.send_text(message), 0.1)
                except asyncio.TimeoutError as e:
                    print("ERROR WS:", e)
                    pass