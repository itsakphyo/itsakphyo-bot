"""
HTTP handlers for webhook and API endpoints.
"""
import logging
from typing import Dict, Any
from fastapi import HTTPException, Request, BackgroundTasks
from app.services.telegram_service import bot_service

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
            logger.info(f"Webhook processed: {result['status']}")
            
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}")
    
    @staticmethod
    async def health_check() -> Dict[str, Any]:
        """Health check endpoint."""
        try:
            # Check bot service status
            bot_status = "healthy" if bot_service.application else "unhealthy"
            
            return {
                "status": "healthy",
                "service": "itsakphyo-bot",
                "bot_status": bot_status,
                "timestamp": None
            }
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
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
