from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import numpy as np
import random 
import uvicorn

class ConnectionManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: bytes):
        for connection in self.active_connections:
            if connection.client_state == WebSocketState.CONNECTED:
                await connection.send_bytes(message)

app = FastAPI()
manager = ConnectionManager()

@app.get('/')
async def health_check():
    return {'status': 'Audio test service running'}

@app.websocket("/audio")
async def audio_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        while True:
            audio_data = await websocket.receive_bytes()
            
            mock_score = random.random()  # Random float between 0.0 and 1.0
            print("Tic" if mock_score > 0.5 else "Toc")  # Using 0.5 as threshold for testing
            
            # Broadcast to all clients
            await manager.broadcast(audio_data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Error processing audio: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)