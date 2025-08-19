"""
WebSocket handlers for real-time communication.
"""
import json
import logging
import uuid
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Depends, Query
from app.core.websocket_manager import ws_manager

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """Handler for WebSocket connections and messages."""
    
    @staticmethod
    async def websocket_endpoint(
        websocket: WebSocket,
        user_id: Optional[str] = Query(None),
        chat_id: Optional[str] = Query(None),
        client_id: Optional[str] = Query(None)
    ):
        """WebSocket endpoint for real-time communication."""
        
        # Generate connection ID
        connection_id = client_id or str(uuid.uuid4())
        
        try:
            # Accept the WebSocket connection
            await websocket.accept()
            
            # Register the connection
            await ws_manager.connect(websocket, connection_id, user_id, chat_id)
            
            # Send welcome message
            await websocket.send_text(json.dumps({
                "type": "connection",
                "event": "connected",
                "data": {
                    "connection_id": connection_id,
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "message": "WebSocket connected successfully"
                },
                "timestamp": None
            }))
            
            # Listen for messages
            while True:
                try:
                    # Receive message from client
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Process the message
                    await WebSocketHandler._process_client_message(
                        connection_id, user_id, chat_id, message
                    )
                    
                except WebSocketDisconnect:
                    logger.info(f"WebSocket client {connection_id} disconnected")
                    break
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from {connection_id}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "event": "invalid_json",
                        "data": {"message": "Invalid JSON format"},
                        "timestamp": None
                    }))
                except Exception as e:
                    logger.error(f"Error processing message from {connection_id}: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "event": "processing_error",
                        "data": {"message": str(e)},
                        "timestamp": None
                    }))
        
        except Exception as e:
            logger.error(f"WebSocket error for {connection_id}: {e}")
        
        finally:
            # Unregister the connection
            await ws_manager.disconnect(connection_id)
    
    @staticmethod
    async def _process_client_message(
        connection_id: str,
        user_id: Optional[str],
        chat_id: Optional[str],
        message: Dict[str, Any]
    ):
        """Process incoming message from WebSocket client."""
        
        message_type = message.get("type")
        event = message.get("event")
        data = message.get("data", {})
        
        logger.info(f"Processing WebSocket message: {message_type}/{event} from {connection_id}")
        
        # Handle different message types
        if message_type == "ping":
            await WebSocketHandler._handle_ping(connection_id)
        
        elif message_type == "chat":
            await WebSocketHandler._handle_chat_message(connection_id, user_id, chat_id, data)
        
        elif message_type == "status":
            await WebSocketHandler._handle_status_request(connection_id)
        
        elif message_type == "subscribe":
            await WebSocketHandler._handle_subscription(connection_id, user_id, chat_id, data)
        
        else:
            logger.warning(f"Unknown message type: {message_type}")
            # Echo back unknown messages
            await ws_manager._send_to_connections({connection_id}, {
                "type": "echo",
                "event": "unknown_message",
                "data": message,
                "timestamp": None
            })
    
    @staticmethod
    async def _handle_ping(connection_id: str):
        """Handle ping message."""
        await ws_manager._send_to_connections({connection_id}, {
            "type": "pong",
            "event": "response",
            "data": {"message": "pong"},
            "timestamp": None
        })
    
    @staticmethod
    async def _handle_chat_message(
        connection_id: str,
        user_id: Optional[str],
        chat_id: Optional[str],
        data: Dict[str, Any]
    ):
        """Handle chat message from WebSocket client."""
        
        message_text = data.get("message", "")
        target_chat = data.get("target_chat_id", chat_id)
        target_user = data.get("target_user_id")
        
        # Prepare message
        chat_message = {
            "type": "chat",
            "event": "message_received",
            "data": {
                "from_connection": connection_id,
                "from_user": user_id,
                "from_chat": chat_id,
                "message": message_text,
                "timestamp": None
            }
        }
        
        # Send to specific targets or broadcast
        if target_user:
            await ws_manager.send_personal_message(target_user, chat_message)
        elif target_chat:
            await ws_manager.send_chat_message(target_chat, chat_message)
        else:
            # Broadcast to all connections except sender
            await ws_manager.broadcast(chat_message, exclude_connections={connection_id})
    
    @staticmethod
    async def _handle_status_request(connection_id: str):
        """Handle status request."""
        stats = await ws_manager.get_connection_stats()
        
        await ws_manager._send_to_connections({connection_id}, {
            "type": "status",
            "event": "response",
            "data": stats,
            "timestamp": None
        })
    
    @staticmethod
    async def _handle_subscription(
        connection_id: str,
        user_id: Optional[str],
        chat_id: Optional[str],
        data: Dict[str, Any]
    ):
        """Handle subscription request."""
        
        subscribe_to = data.get("subscribe_to", [])
        
        # This is a placeholder for subscription logic
        # In a real application, you might want to implement
        # topic-based subscriptions, event filtering, etc.
        
        response = {
            "type": "subscription",
            "event": "confirmed",
            "data": {
                "subscribed_to": subscribe_to,
                "user_id": user_id,
                "chat_id": chat_id,
                "message": "Subscription processed"
            },
            "timestamp": None
        }
        
        await ws_manager._send_to_connections({connection_id}, response)
    
    @staticmethod
    async def broadcast_system_message(message: str, message_type: str = "system"):
        """Broadcast a system message to all connected clients."""
        system_message = {
            "type": message_type,
            "event": "system_broadcast",
            "data": {
                "message": message,
                "timestamp": None
            }
        }
        
        await ws_manager.broadcast(system_message)
        logger.info(f"Broadcasted system message: {message}")


# Handler instance
websocket_handler = WebSocketHandler()
