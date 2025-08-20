"""
Telegram bot service for handling webhook and WebSocket integration.
"""
import asyncio
import json
import logging
from typing import Optional, Dict, Any
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from app.core.websocket_manager import ws_manager
from config.settings import settings

logger = logging.getLogger(__name__)


class TelegramBotService:
    """Service for managing Telegram bot operations."""
    
    def __init__(self):
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None
        self.polling_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize the Telegram bot application."""
        try:
            # Check if we're in demo mode (invalid token)
            if settings.is_demo_mode:
                logger.info("Running in demo mode - Telegram bot disabled")
                return
            
            # Create application
            self.application = Application.builder().token(settings.telegram_token).build()
            self.bot = self.application.bot
            
            # Add handlers
            self._setup_handlers()
            
            # Initialize application
            await self.application.initialize()
            await self.application.start()
            
            # Start polling if no webhook URL is configured
            if not settings.webhook_full_url:
                logger.info("No webhook URL configured, starting polling...")
                # Remove any existing webhook first
                try:
                    bot_instance = self.bot
                    if bot_instance:
                        await bot_instance.delete_webhook(drop_pending_updates=True) # type: ignore
                except Exception as e:
                    logger.warning(f"Failed to delete webhook: {e}")
                
                # Start polling in a background task
                self.polling_task = asyncio.create_task(self._start_polling())
                logger.info("Polling task started successfully")
            else:
                logger.info("Webhook URL configured, polling disabled")
            
            logger.info("Telegram bot service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot service: {e}")
            logger.info("Continuing without Telegram bot functionality...")
            # Don't raise in demo mode, just continue without bot functionality
    
    async def _start_polling(self):
        """Start polling for updates in a background task."""
        try:
            if self.application and self.application.updater:
                logger.info("Starting updater polling...")
                await self.application.updater.start_polling(
                    poll_interval=1.0,
                    timeout=10,
                    bootstrap_retries=-1,
                    read_timeout=10,
                    write_timeout=10,
                    connect_timeout=10,
                    pool_timeout=10,
                )
                logger.info("Updater polling started successfully")
        except Exception as e:
            logger.error(f"Error in polling task: {e}")
    
    async def shutdown(self):
        """Shutdown the Telegram bot service."""
        if self.application:
            try:
                # Stop polling task if it's running
                if self.polling_task and not self.polling_task.done():
                    self.polling_task.cancel()
                    try:
                        await self.polling_task
                    except asyncio.CancelledError:
                        pass
                    logger.info("Polling task cancelled")
                
                # Stop updater if it's running
                if self.application.updater and self.application.updater.running:
                    await self.application.updater.stop()
                    logger.info("Updater stopped")
                
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Telegram bot service shutdown successfully")
            except Exception as e:
                logger.error(f"Error during bot service shutdown: {e}")
    
    def _setup_handlers(self):
        """Setup message and command handlers."""
        if not self.application:
            return
        
        # Command handlers
        self.application.add_handler(CommandHandler('start', self._start_command))
        self.application.add_handler(CommandHandler('help', self._help_command))
        self.application.add_handler(CommandHandler('stop', self._stop_command))
        
        # Message handler
        self.application.add_handler(MessageHandler(filters.TEXT, self._handle_message))
        
        # Error handler
        self.application.add_error_handler(self._error_handler)
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        if update.message is None:
            return
            
        user_id = str(update.effective_user.id) if update.effective_user else None
        chat_id = str(update.effective_chat.id) if update.effective_chat else None
        
        response_text = (
            "🤖 Hello! Welcome to the bot.\n\n"
            "Available commands:\n"
            "/help - Show this help message\n"
            "/stop - Stop the bot\n\n"
            "Feel free to send me any message!"
        )
        
        await update.message.reply_text(response_text)
        
        # Broadcast to WebSocket connections
        await self._broadcast_telegram_message(update, "start_command", {
            "command": "start",
            "user_id": user_id,
            "chat_id": chat_id,
            "response": response_text
        })
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        if update.message is None:
            return
            
        response_text = (
            "🆘 Help - Bot Commands:\n\n"
            "/start - Initialize the bot\n"
            "/help - Show this help message\n"
            "/stop - Stop the bot\n\n"
            "Send me any message and I'll respond!"
        )
        
        await update.message.reply_text(response_text)
        
        # Broadcast to WebSocket connections
        user_id = str(update.effective_user.id) if update.effective_user else None
        chat_id = str(update.effective_chat.id) if update.effective_chat else None
        
        await self._broadcast_telegram_message(update, "help_command", {
            "command": "help",
            "user_id": user_id,
            "chat_id": chat_id,
            "response": response_text
        })
    
    async def _stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command."""
        if update.message is None:
            return
            
        response_text = "👋 Goodbye! Bot is stopping..."
        await update.message.reply_text(response_text)
        
        # Broadcast to WebSocket connections
        user_id = str(update.effective_user.id) if update.effective_user else None
        chat_id = str(update.effective_chat.id) if update.effective_chat else None
        
        await self._broadcast_telegram_message(update, "stop_command", {
            "command": "stop",
            "user_id": user_id,
            "chat_id": chat_id,
            "response": response_text
        })
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        if update.message is None or update.message.text is None:
            return
        
        message_type = update.message.chat.type
        text = update.message.text
        user_id = str(update.effective_user.id) if update.effective_user else None
        chat_id = str(update.effective_chat.id) if update.effective_chat else None
        
        # Process message based on chat type
        if message_type == 'group':
            if settings.bot_username and settings.bot_username in text:
                new_text = text.replace(settings.bot_username, '').strip()
                response = self._simple_response(new_text)
            else:
                return
        else:
            response = self._simple_response(text)
        
        await update.message.reply_text(response)
        
        # Broadcast to WebSocket connections
        await self._broadcast_telegram_message(update, "message", {
            "user_id": user_id,
            "chat_id": chat_id,
            "message": text,
            "response": response
        })
        
        # You can add your own reply logic here for more complex messages
    
    def _generate_response(self, text: str) -> str:
        """Generate response to user message."""
        return self._simple_response(text)

    def _simple_response(self, text: str) -> str:
        """Simple greeting and thank you responses only."""
        t = text.lower().strip()
        if t in ['hello', 'hi', 'hey']:
            return "Hello!"
        elif t in ['thanks', 'thank you']:
            return "Thank you!"
        else:
            return "Thank you for your message."
    
    async def _broadcast_telegram_message(self, update: Update, event_type: str, data: Dict[str, Any]):
        """Broadcast Telegram message data to WebSocket connections."""
        try:
            message_data = {
                "type": "telegram_message",
                "event": event_type,
                "data": data,
                "timestamp": update.message.date.isoformat() if update.message and update.message.date else None
            }
            
            user_id = data.get("user_id")
            chat_id = data.get("chat_id")
            
            # Send to specific user connections if available
            if user_id:
                await ws_manager.send_personal_message(user_id, message_data)
            
            # Send to specific chat connections if available
            if chat_id and chat_id != user_id:
                await ws_manager.send_chat_message(chat_id, message_data)
                
        except Exception as e:
            logger.error(f"Error broadcasting telegram message: {e}")
    
    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        error_msg = f'Update {update} caused error {context.error}'
        logger.error(error_msg)
        
        # Broadcast error to WebSocket connections if possible
        try:
            error_data = {
                "type": "error",
                "event": "telegram_error",
                "data": {
                    "error": str(context.error),
                    "update": str(update)
                },
                "timestamp": None
            }
            await ws_manager.broadcast(error_data)
        except Exception as e:
            logger.error(f"Error broadcasting error message: {e}")
    
    async def process_webhook(self, update_data: dict) -> Dict[str, Any]:
        """Process incoming webhook update."""
        try:
            if not self.application or not self.bot:
                logger.warning("Bot not initialized, cannot process webhook")
                return {
                    "status": "error",
                    "message": "Bot not initialized"
                }
            
            # Create Update object from webhook data
            update = Update.de_json(update_data, self.bot)
            
            if update:
                # Process the update
                await self.application.process_update(update)
                
                return {
                    "status": "success",
                    "message": "Update processed successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": "Invalid update data"
                }
                
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def configure_webhook(self, webhook_url: str) -> bool:
        """Set the webhook URL for the bot."""
        try:
            if self.bot is None:
                logger.warning("Cannot set webhook: Telegram bot is not initialized")
                return False
            
            # Use the correct method call
            bot_instance = self.bot
            result = await bot_instance.set_webhook(url=webhook_url)  # type: ignore
            logger.info(f"Webhook set successfully: {webhook_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
            return False
    
    async def remove_webhook(self) -> bool:
        """Delete the webhook for the bot."""
        try:
            if self.bot is None:
                logger.warning("Cannot delete webhook: Telegram bot is not initialized")
                return False
            
            bot_instance = self.bot
            await bot_instance.delete_webhook()  # type: ignore
            logger.info("Webhook deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete webhook: {e}")
            return False


# Global bot service instance
bot_service = TelegramBotService()
