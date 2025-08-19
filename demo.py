"""
Demo/test version of the bot that doesn't require Telegram token.
Use this to test the WebSocket functionality without setting up a bot.
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import os
import uvicorn
from fastapi import FastAPI, WebSocket, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional

# Mock settings for demo
class DemoSettings:
    host = "0.0.0.0"
    port = 8000
    environment = "demo"
    websocket_path = "/ws"
    log_level = "INFO"
    ping_interval = 20
    ping_timeout = 10

settings = DemoSettings()

# Create FastAPI app
app = FastAPI(
    title="Itsakphyo Bot Demo",
    description="Demo WebSocket Bot (No Telegram Required)",
    version="1.0.0-demo"
)

# Simple WebSocket manager for demo
class DemoWebSocketManager:
    def __init__(self):
        self.connections = {}
        self.connection_count = 0
    
    async def connect(self, websocket, connection_id, user_id=None, chat_id=None):
        self.connections[connection_id] = {
            "websocket": websocket,
            "user_id": user_id,
            "chat_id": chat_id
        }
        self.connection_count += 1
        print(f"WebSocket connected: {connection_id}")
    
    async def disconnect(self, connection_id):
        if connection_id in self.connections:
            del self.connections[connection_id]
        print(f"WebSocket disconnected: {connection_id}")
    
    async def send_message(self, connection_id, message):
        if connection_id in self.connections:
            websocket = self.connections[connection_id]["websocket"]
            await websocket.send_text(message)
    
    async def broadcast(self, message):
        for conn_data in self.connections.values():
            try:
                await conn_data["websocket"].send_text(message)
            except:
                pass
    
    def get_stats(self):
        return {
            "total_connections": len(self.connections),
            "connection_count": self.connection_count
        }

ws_manager = DemoWebSocketManager()

@app.get("/")
async def root():
    return {
        "message": "Itsakphyo Bot Demo",
        "version": "1.0.0-demo",
        "status": "running",
        "note": "This is a demo version - no Telegram token required"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "itsakphyo-bot-demo",
        "websocket_stats": ws_manager.get_stats()
    }

@app.get("/stats")
async def stats():
    return {
        "status": "success",
        "data": ws_manager.get_stats()
    }

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None),
    chat_id: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None)
):
    connection_id = client_id or f"demo_{len(ws_manager.connections)}"
    
    await websocket.accept()
    await ws_manager.connect(websocket, connection_id, user_id, chat_id)
    
    try:
        # Send welcome message
        welcome_msg = f'{{"type": "connection", "event": "connected", "data": {{"connection_id": "{connection_id}", "message": "Demo WebSocket connected!"}}}}'
        await websocket.send_text(welcome_msg)
        
        while True:
            data = await websocket.receive_text()
            print(f"Received from {connection_id}: {data}")
            
            # Echo back with demo response
            import json
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    response = '{"type": "pong", "event": "response", "data": {"message": "pong from demo"}}'
                else:
                    response = f'{{"type": "echo", "event": "demo_response", "data": {{"original": {data}, "from": "{connection_id}"}}}}'
                
                await websocket.send_text(response)
            except:
                await websocket.send_text(f'{{"type": "error", "event": "parse_error", "data": {{"message": "Could not parse JSON"}}}}')
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(connection_id)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    @app.get("/dashboard")
    async def dashboard():
        return FileResponse("static/dashboard.html")
except:
    print("Could not mount static files - dashboard not available")

if __name__ == "__main__":
    print("🚀 Starting Itsakphyo Bot Demo")
    print("📊 Dashboard: http://localhost:8000/dashboard")
    print("🔌 WebSocket: ws://localhost:8000/ws")
    print("💡 This demo doesn't require Telegram credentials")
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower()
    )
