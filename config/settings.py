"""
Application configuration settings.
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings configuration."""
    
    def __init__(self):
        # Bot Configuration
        self.telegram_token = os.getenv("TOKEN", "")
        self.bot_username = os.getenv("BOT_USERNAME", "")
        self.webhook_url = os.getenv("WEBHOOK_URL")
        self.webhook_path = os.getenv("WEBHOOK_PATH", "/webhook")
        
        # Server Configuration
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        self.debug = os.getenv("DEBUG", "False").lower() == "true"
        
        # Security
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.allowed_hosts = ["*"]
        self.cors_origins = ["*"]
        
        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "logs/app.log")
        self.log_max_size = int(os.getenv("LOG_MAX_SIZE", "10485760"))  # 10MB
        self.log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
        
        # Environment
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        # Google Cloud RAG Configuration
        self.google_cloud_project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        self.google_cloud_region = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
        self.google_drive_folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        
        # Validate required settings
        self._validate()
    
    def _validate(self):
        """Validate that required settings are set."""
        if not self.telegram_token:
            raise ValueError('TOKEN environment variable must be set')
        
        # Allow demo tokens for testing
        if self.telegram_token in ["your_telegram_bot_token_here", "demo_token_for_testing"]:
            print("⚠️  Warning: Using demo/placeholder token - Telegram functionality will be disabled")
        
        if not self.bot_username:
            raise ValueError('BOT_USERNAME environment variable must be set')
        
        # Clean bot username (remove @ if present)
        if self.bot_username.startswith('@'):
            self.bot_username = self.bot_username[1:]
        
        # Allow demo usernames for testing  
        if self.bot_username in ["your_bot_username_here", "demo_bot"]:
            print("⚠️  Warning: Using demo/placeholder bot username")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode with placeholder credentials."""
        return self.telegram_token in ["your_telegram_bot_token_here", "demo_token_for_testing"]
    
    @property
    def webhook_full_url(self) -> Optional[str]:
        """Get full webhook URL."""
        if self.webhook_url:
            return f"{self.webhook_url.rstrip('/')}{self.webhook_path}"
        return None


# Global settings instance
settings = Settings()
