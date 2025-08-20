"""
Data models for the application.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class MessageType(Enum):
    """Types of messages."""
    TEXT = "text"
    COMMAND = "command"
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    VOICE = "voice"
    STICKER = "sticker"
    LOCATION = "location"
    CONTACT = "contact"


@dataclass
class TelegramUser:
    """Telegram user data model."""
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_bot: bool = False
    
    @property
    def full_name(self) -> str:
        """Get full name of the user."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
    
    @property
    def mention(self) -> str:
        """Get user mention."""
        if self.username:
            return f"@{self.username}"
        return self.full_name


@dataclass
class TelegramChat:
    """Telegram chat data model."""
    id: int
    type: str
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @property
    def display_name(self) -> str:
        """Get display name for the chat."""
        if self.title:
            return self.title
        if self.first_name:
            if self.last_name:
                return f"{self.first_name} {self.last_name}"
            return self.first_name
        if self.username:
            return f"@{self.username}"
        return f"Chat {self.id}"


@dataclass
class TelegramMessage:
    """Telegram message data model."""
    message_id: int
    user: TelegramUser
    chat: TelegramChat
    date: datetime
    text: Optional[str] = None
    message_type: MessageType = MessageType.TEXT
    reply_to_message_id: Optional[int] = None
    forward_from: Optional[TelegramUser] = None
    entities: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def is_command(self) -> bool:
        """Check if message is a command."""
        return self.message_type == MessageType.COMMAND or (
            bool(self.text) and self.text.startswith('/')
        )
    
    @property
    def command(self) -> Optional[str]:
        """Extract command from message."""
        if self.is_command and self.text:
            command_text = self.text.split()[0]
            return command_text[1:]  # Remove the '/' prefix
        return None
    
    @property
    def command_args(self) -> List[str]:
        """Extract command arguments."""
        if self.is_command and self.text:
            parts = self.text.split()[1:]
            return parts
        return []


@dataclass
class BotStats:
    """Bot statistics data model."""
    total_messages_processed: int = 0
    total_commands_processed: int = 0
    uptime_seconds: float = 0
    last_update_timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_messages_processed": self.total_messages_processed,
            "total_commands_processed": self.total_commands_processed,
            "uptime_seconds": self.uptime_seconds,
            "last_update_timestamp": self.last_update_timestamp.isoformat() if self.last_update_timestamp else None
        }


@dataclass
class APIResponse:
    """Standard API response model."""
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "status": self.status,
            "message": self.message,
            "data": self.data,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
