"""
WebSocket connection manager for handling real-time connections.
"""
import json
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""
    user_id: Optional[str] = None
    chat_id: Optional[str] = None
    connected_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    
    def __post_init__(self):
        if self.connected_at is None:
            self.connected_at = datetime.utcnow()
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        self._connections: Dict[str, Any] = {}  # websocket -> ConnectionInfo
        self._user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self._chat_connections: Dict[str, Set[str]] = {}  # chat_id -> set of connection_ids
        self._connection_info: Dict[str, ConnectionInfo] = {}  # connection_id -> ConnectionInfo
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: Any, connection_id: str, user_id: Optional[str] = None, chat_id: Optional[str] = None):
        """Register a new WebSocket connection."""
        async with self._lock:
            # Store connection
            self._connections[connection_id] = websocket
            
            # Create connection info
            conn_info = ConnectionInfo(user_id=user_id, chat_id=chat_id)
            self._connection_info[connection_id] = conn_info
            
            # Index by user_id
            if user_id:
                if user_id not in self._user_connections:
                    self._user_connections[user_id] = set()
                self._user_connections[user_id].add(connection_id)
            
            # Index by chat_id
            if chat_id:
                if chat_id not in self._chat_connections:
                    self._chat_connections[chat_id] = set()
                self._chat_connections[chat_id].add(connection_id)
            
            logger.info(f"WebSocket connected: {connection_id}, user: {user_id}, chat: {chat_id}")
            logger.info(f"Total connections: {len(self._connections)}")
    
    async def disconnect(self, connection_id: str):
        """Unregister a WebSocket connection."""
        async with self._lock:
            if connection_id not in self._connections:
                return
            
            # Get connection info
            conn_info = self._connection_info.get(connection_id)
            
            # Remove from main connections
            del self._connections[connection_id]
            
            # Remove from user connections
            if conn_info and conn_info.user_id:
                user_connections = self._user_connections.get(conn_info.user_id, set())
                user_connections.discard(connection_id)
                if not user_connections:
                    del self._user_connections[conn_info.user_id]
            
            # Remove from chat connections
            if conn_info and conn_info.chat_id:
                chat_connections = self._chat_connections.get(conn_info.chat_id, set())
                chat_connections.discard(connection_id)
                if not chat_connections:
                    del self._chat_connections[conn_info.chat_id]
            
            # Remove connection info
            if connection_id in self._connection_info:
                del self._connection_info[connection_id]
            
            logger.info(f"WebSocket disconnected: {connection_id}")
            logger.info(f"Total connections: {len(self._connections)}")
    
    async def send_personal_message(self, user_id: str, message: dict):
        """Send a message to all connections of a specific user."""
        connection_ids = self._user_connections.get(user_id, set()).copy()
        
        if not connection_ids:
            logger.warning(f"No active connections for user: {user_id}")
            return
        
        await self._send_to_connections(connection_ids, message)
    
    async def send_chat_message(self, chat_id: str, message: dict):
        """Send a message to all connections of a specific chat."""
        connection_ids = self._chat_connections.get(chat_id, set()).copy()
        
        if not connection_ids:
            logger.warning(f"No active connections for chat: {chat_id}")
            return
        
        await self._send_to_connections(connection_ids, message)
    
    async def broadcast(self, message: dict, exclude_connections: Optional[Set[str]] = None):
        """Broadcast a message to all connections."""
        exclude_connections = exclude_connections or set()
        connection_ids = set(self._connections.keys()) - exclude_connections
        
        await self._send_to_connections(connection_ids, message)
    
    async def _send_to_connections(self, connection_ids: Set[str], message: dict):
        """Send message to specific connections."""
        if not connection_ids:
            return
        
        # Prepare message
        message_str = json.dumps(message, default=str)
        
        # Send to all connections
        disconnect_list = []
        
        for connection_id in connection_ids:
            websocket = self._connections.get(connection_id)
            if websocket:
                try:
                    await websocket.send_text(message_str)
                    # Update last activity
                    if connection_id in self._connection_info:
                        conn_info = self._connection_info[connection_id]
                        if conn_info.last_activity is not None:
                            conn_info.last_activity = datetime.utcnow()
                except Exception as e:
                    logger.error(f"Error sending message to {connection_id}: {e}")
                    disconnect_list.append(connection_id)
        
        # Clean up failed connections
        for connection_id in disconnect_list:
            await self.disconnect(connection_id)
    
    async def get_connection_stats(self) -> dict:
        """Get connection statistics."""
        return {
            "total_connections": len(self._connections),
            "users_connected": len(self._user_connections),
            "chats_connected": len(self._chat_connections),
            "connections_by_user": {
                user_id: len(connections) 
                for user_id, connections in self._user_connections.items()
            },
            "connections_by_chat": {
                chat_id: len(connections) 
                for chat_id, connections in self._chat_connections.items()
            }
        }
    
    async def cleanup_stale_connections(self, max_idle_minutes: int = 30):
        """Clean up connections that have been idle for too long."""
        current_time = datetime.utcnow()
        stale_connections = []
        
        for connection_id, conn_info in self._connection_info.items():
            if conn_info.last_activity:
                idle_time = (current_time - conn_info.last_activity).total_seconds() / 60
                if idle_time > max_idle_minutes:
                    stale_connections.append(connection_id)
        
        for connection_id in stale_connections:
            logger.info(f"Cleaning up stale connection: {connection_id}")
            await self.disconnect(connection_id)
        
        return len(stale_connections)


# Global WebSocket manager instance
ws_manager = WebSocketManager()
