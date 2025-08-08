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