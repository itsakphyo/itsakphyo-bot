"""
HTTP handlers for webhook and API endpoints.
"""
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request, BackgroundTasks
from app.services.telegram_service import bot_service
from app.handlers.websocket_handler import websocket_handler
from app.core.websocket_manager import ws_manager

logger = logging.getLogger(__name__)


class HTTPHandler:
    """Handler for HTTP requests including webhooks."""
    
    @staticmethod
    async def webhook_handler(request: Request, background_tasks: BackgroundTasks) -> Dict[str, str]:
        """Handle incoming Telegram webhook requests."""
        try:
            # Get the raw update data
            update_data = await request.json()
            
            logger.info(f"Received webhook update: {update_data}")
            
            # Process the update in the background
            background_tasks.add_task(
                HTTPHandler._process_webhook_update, update_data
            )
            
            return {"status": "ok"}
            
        except Exception as e:
            logger.error(f"Webhook handler error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @staticmethod
    async def _process_webhook_update(update_data: Dict[str, Any]):
        """Process webhook update in background."""
        try:
            # Process through bot service
            result = await bot_service.process_webhook(update_data)
            
            # Broadcast webhook processing result to WebSocket clients
            await websocket_handler.broadcast_system_message(
                f"Webhook processed: {result['status']}",
                "webhook_status"
            )
            
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}")
    
    @staticmethod
    async def health_check() -> Dict[str, Any]:
        """Health check endpoint."""
        try:
            # Get connection stats
            ws_stats = await ws_manager.get_connection_stats()
            
            # Check bot service status
            bot_status = "healthy" if bot_service.application else "unhealthy"
            
            return {
                "status": "healthy",
                "service": "itsakphyo-bot",
                "bot_status": bot_status,
                "websocket_stats": ws_stats,
                "timestamp": None
            }
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    async def get_connection_stats() -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        try:
            stats = await ws_manager.get_connection_stats()
            return {
                "status": "success",
                "data": stats
            }
        except Exception as e:
            logger.error(f"Error getting connection stats: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    async def broadcast_message(
        message: str,
        message_type: str = "admin",
        target_user: Optional[str] = None,
        target_chat: Optional[str] = None
    ) -> Dict[str, str]:
        """Broadcast a message to WebSocket connections."""
        try:
            broadcast_data = {
                "type": message_type,
                "event": "admin_broadcast",
                "data": {
                    "message": message,
                    "from": "admin",
                    "timestamp": None
                }
            }
            
            if target_user:
                await ws_manager.send_personal_message(target_user, broadcast_data)
                return {"status": "success", "message": f"Message sent to user {target_user}"}
            
            elif target_chat:
                await ws_manager.send_chat_message(target_chat, broadcast_data)
                return {"status": "success", "message": f"Message sent to chat {target_chat}"}
            
            else:
                await ws_manager.broadcast(broadcast_data)
                return {"status": "success", "message": "Message broadcasted to all connections"}
                
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    async def cleanup_connections() -> Dict[str, Any]:
        """Cleanup stale WebSocket connections."""
        try:
            cleaned_count = await ws_manager.cleanup_stale_connections()
            
            return {
                "status": "success",
                "message": f"Cleaned up {cleaned_count} stale connections"
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up connections: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    async def set_webhook(webhook_url: str) -> Dict[str, Any]:
        """Set the Telegram webhook URL."""
        try:
            success = await bot_service.configure_webhook(webhook_url)
            
            if success:
                return {
                    "status": "success",
                    "message": f"Webhook set to {webhook_url}"
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to set webhook")
                
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    async def delete_webhook() -> Dict[str, Any]:
        """Delete the Telegram webhook."""
        try:
            success = await bot_service.remove_webhook()
            
            if success:
                return {
                    "status": "success",
                    "message": "Webhook deleted successfully"
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to delete webhook")
                
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# Handler instance
http_handler = HTTPHandler()
