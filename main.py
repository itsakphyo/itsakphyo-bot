"""
Main application entry point.
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.main import app

if __name__ == "__main__":
    import uvicorn
    from config.settings import settings
    
    print(f"Starting Itsakphyo Bot v1.0.0")
    print(f"Environment: {settings.environment}")
    print(f"Host: {settings.host}:{settings.port}")
    print(f"Webhook endpoint: {settings.webhook_path}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=not settings.is_production,
        log_level=settings.log_level.lower(),
        access_log=True,
    )