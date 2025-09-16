# app/websocket/manager.py
from typing import List
from fastapi import WebSocket

class ConnectionManager:
    """WebSocket connection manager for handling real-time communication"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket connection"""
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all active connections"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Connection is broken, remove it
                self.disconnect(connection)