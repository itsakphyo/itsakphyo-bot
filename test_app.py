#!/usr/bin/env python3
"""
Test script to debug app startup issues
"""

print("Starting app test...")

try:
    print("Testing basic imports...")
    import sys
    import os
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    print("Testing FastAPI import...")
    from fastapi import FastAPI
    print("✅ FastAPI imported successfully")
    
    print("Testing config imports...")
    from config.settings import settings
    print("✅ Settings imported successfully")
    print(f"Bot token configured: {'yes' if settings.telegram_token else 'no'}")
    
    print("Testing logging config...")
    from config.logging import setup_logging, get_logger
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Logging setup successful")
    print("✅ Logging imported successfully")
    
    print("Testing telegram service...")
    from app.services.telegram_service import bot_service
    print("✅ Telegram service imported successfully")
    
    print("Testing http handler...")
    from app.handlers.http_handler import HTTPHandler
    print("✅ HTTP handler imported successfully")
    
    print("Testing main app import...")
    from app.main import app
    print("✅ Main app imported successfully")
    
    print("Testing basic FastAPI functionality...")
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/")
    print(f"Root endpoint response: {response.status_code}")
    print(f"Response data: {response.json()}")
    
    print("🎉 All tests successful!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
