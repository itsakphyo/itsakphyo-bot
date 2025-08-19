"""
FastAPI application setup and configuration.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Request, BackgroundTasks, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, Dict, Any

from config.settings import settings
from config.logging import setup_logging, get_logger
from app.services.telegram_service import bot_service
from app.handlers.websocket_handler import WebSocketHandler
from app.handlers.http_handler import HTTPHandler
from app.core.websocket_manager import ws_manager

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting application...")
    
    try:
        # Initialize bot service
        await bot_service.initialize()
        
        # Set webhook if configured
        if settings.webhook_full_url:
            webhook_success = await bot_service.configure_webhook(settings.webhook_full_url)
            if webhook_success:
                logger.info(f"Webhook set to: {settings.webhook_full_url}")
            else:
                logger.warning("Failed to set webhook")
        
        logger.info("Application started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    try:
        # Cleanup WebSocket connections
        await ws_manager.cleanup_stale_connections(max_idle_minutes=0)
        
        # Shutdown bot service
        await bot_service.shutdown()
        
        logger.info("Application shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during application shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="Itsakphyo Bot",
    description="Production-ready WebSocket-enabled Telegram Bot",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )


# Routes

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Itsakphyo Bot API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return await HTTPHandler.health_check()


@app.post(settings.webhook_path)
async def webhook(request: Request, background_tasks: BackgroundTasks):
    """Telegram webhook endpoint."""
    return await HTTPHandler.webhook_handler(request, background_tasks)


@app.websocket(settings.websocket_path)
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None),
    chat_id: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None)
):
    """WebSocket endpoint for real-time communication."""
    await WebSocketHandler.websocket_endpoint(websocket, user_id, chat_id, client_id)


@app.get("/stats")
async def get_stats():
    """Get connection statistics."""
    return await HTTPHandler.get_connection_stats()


@app.post("/broadcast")
async def broadcast_message(
    message: str = Query(..., description="Message to broadcast"),
    message_type: str = Query("admin", description="Type of message"),
    target_user: Optional[str] = Query(None, description="Target user ID"),
    target_chat: Optional[str] = Query(None, description="Target chat ID")
):
    """Broadcast message to WebSocket connections."""
    return await HTTPHandler.broadcast_message(message, message_type, target_user, target_chat)


@app.post("/cleanup")
async def cleanup_connections():
    """Cleanup stale WebSocket connections."""
    return await HTTPHandler.cleanup_connections()


@app.post("/webhook/set")
async def set_webhook(webhook_url: str = Query(..., description="Webhook URL to set")):
    """Set Telegram webhook URL."""
    return await HTTPHandler.set_webhook(webhook_url)


@app.delete("/webhook")
async def delete_webhook():
    """Delete Telegram webhook."""
    return await HTTPHandler.delete_webhook()


# Add static files for dashboard
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    @app.get("/dashboard")
    async def dashboard():
        """Serve the dashboard."""
        from fastapi.responses import FileResponse
        return FileResponse("static/dashboard.html")
        
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=not settings.is_production,
        log_level=settings.log_level.lower(),
        access_log=True,
    )
