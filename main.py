# import os
# import asyncio
# import logging
# from typing import Final

# from dotenv import load_dotenv
# from flask import Flask, request, abort
# from telegram import Update
# from telegram.ext import (
#     Application,
#     CommandHandler,
#     MessageHandler,
#     ContextTypes,
#     filters,
# )

# # Load environment
# load_dotenv()
# TOKEN: Final = os.getenv("TOKEN")
# BOT_USERNAME: Final = os.getenv("BOT_USERNAME", "")

# if not TOKEN:
#     raise RuntimeError("Environment variable TOKEN is required")

# # Configure logging
# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     level=logging.INFO,
# )
# logger = logging.getLogger(__name__)

# # Create Flask app
# app = Flask(__name__)

# # Create the Telegram bot application
# bot_app = Application.builder().token(TOKEN).build()


# # ——— Bot command handlers ———

# async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Handler for /start."""
#     if update.message:
#         await update.message.reply_text("မင်္ဂလာပါ! Bot ကို ဆက်သွယ်လိုပါက စတင်ပါ။")

# async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Handler for /help."""
#     if update.message:
#         await update.message.reply_text("အသုံးပြုနည်းများ: /start, /help, /stop")

# async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Handler for /stop."""
#     if update.message:
#         await update.message.reply_text("Bot service ကို ရပ်တန့်လိုက်ပြီး ဖြစ်ပါပြီ။")

# # ——— Message logic ———

# def handle_response(text: str) -> str:
#     """Generate a reply based on incoming text."""
#     lower = text.lower()
#     if any(greet in lower for greet in ("hi", "hello")):
#         return "Lee hi"
#     if "lee" in lower:
#         return "လီးလား?"
#     if lower.strip() == "ဟ":
#         return "လီးဟ"
#     if "fuck" in lower:
#         return "😅 ဆက်လက်မေးမြန်းပါ"
#     return "သားသားချစ်တဲ့အားလုံး မဂ်လာပါ!"

# async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Catch-all message handler."""
#     if not update.message or not update.message.text:
#         return

#     chat_type = update.message.chat.type
#     text = update.message.text

#     if chat_type == "group":
#         # Only respond if bot is mentioned in group
#         if BOT_USERNAME and BOT_USERNAME in text:
#             # strip @BotUsername
#             text = text.replace(BOT_USERNAME, "").strip()
#         else:
#             return

#     reply = handle_response(text)
#     await update.message.reply_text(reply)

# async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Log errors."""
#     logger.error("Error handling update %s: %s", update, context.error)


# # ——— Register handlers ———

# bot_app.add_handler(CommandHandler("start", start_command))
# bot_app.add_handler(CommandHandler("help", help_command))
# bot_app.add_handler(CommandHandler("stop", stop_command))
# bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
# bot_app.add_error_handler(error_handler)


# # ——— Flask routes ———

# @app.route("/", methods=["GET"])
# def health_check() -> str:
#     return "OK"

# @app.route("/webhook", methods=["POST"])
# def webhook() -> str:
#     """Receive Telegram update via webhook and dispatch to bot."""
#     if not request.is_json:
#         abort(400, "Expected JSON")

#     update_data = request.get_json()
#     update = Update.de_json(update_data, bot_app.bot)
#     # Process update (runs your handlers)
#     asyncio.run(bot_app.process_update(update))
#     return "OK"


# # Note: no `if __name__ == "__main__"` block, Gunicorn handles startup.
from typing import Final
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os

load_dotenv()

TOKEN: Final = os.getenv("TOKEN")
if TOKEN is None:
    raise ValueError("TOKEN environment variable is not set.")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")

#Commends
async def start_commend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is not None:
        await update.message.reply_text('Hello')
        
async def help_commend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is not None:
        await update.message.reply_text('Help')
        
async def stop_commend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is not None:
        await update.message.reply_text('Stop')

#Handle responses
def handle_response(text: str) -> str:
    return "Hello"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is not None:
        message_type: str = update.message.chat.type
        text: str = update.message.text if update.message.text is not None else ""
    else:
        message_type: str = ""
        text: str = ""

    if message_type == 'group':
        if isinstance(BOT_USERNAME, str) and BOT_USERNAME and BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    
    else:
        response: str = handle_response(text)

    if update.message is not None:
        await update.message.reply_text(response)

async def error_handle(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start_commend))
    app.add_handler(CommandHandler('help', help_commend))
    app.add_handler(CommandHandler('stop', stop_commend))

    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    app.add_error_handler(error_handle)

    print('Polling...')
    app.run_polling(poll_interval=1)