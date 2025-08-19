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


class ConnectionStatus(Enum):
    """WebSocket connection status."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


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
class WebSocketMessage:
    """WebSocket message data model."""
    type: str
    event: str
    data: Dict[str, Any]
    timestamp: Optional[datetime] = None
    connection_id: Optional[str] = None
    user_id: Optional[str] = None
    chat_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "event": self.event,
            "data": self.data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "connection_id": self.connection_id,
            "user_id": self.user_id,
            "chat_id": self.chat_id
        }


@dataclass
class ConnectionMetrics:
    """WebSocket connection metrics."""
    connection_id: str
    user_id: Optional[str]
    chat_id: Optional[str]
    connected_at: datetime
    last_activity: datetime
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    status: ConnectionStatus = ConnectionStatus.CONNECTED
    
    @property
    def uptime_seconds(self) -> float:
        """Get connection uptime in seconds."""
        return (datetime.utcnow() - self.connected_at).total_seconds()
    
    @property
    def idle_seconds(self) -> float:
        """Get idle time in seconds."""
        return (datetime.utcnow() - self.last_activity).total_seconds()
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()


@dataclass
class BotStats:
    """Bot statistics data model."""
    total_messages_processed: int = 0
    total_commands_processed: int = 0
    total_websocket_connections: int = 0
    active_websocket_connections: int = 0
    uptime_seconds: float = 0
    last_update_timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_messages_processed": self.total_messages_processed,
            "total_commands_processed": self.total_commands_processed,
            "total_websocket_connections": self.total_websocket_connections,
            "active_websocket_connections": self.active_websocket_connections,
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
