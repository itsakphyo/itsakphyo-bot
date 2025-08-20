"""
FastAPI application setup and configuration.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any

from config.settings import settings
from config.logging import setup_logging, get_logger
from app.services.telegram_service import bot_service
from app.handlers.http_handler import HTTPHandler

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
        # Shutdown bot service
        await bot_service.shutdown()
        
        logger.info("Application shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during application shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="Itsakphyo Bot",
    description="Production-ready Telegram Bot",
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


@app.post("/webhook/set")
async def set_webhook(webhook_url: str):
    """Set Telegram webhook URL."""
    return await HTTPHandler.set_webhook(webhook_url)


@app.delete("/webhook")
async def delete_webhook():
    """Delete Telegram webhook."""
    return await HTTPHandler.delete_webhook()


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
