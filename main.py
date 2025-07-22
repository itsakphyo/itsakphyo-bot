from typing import Final
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
import asyncio
from flask import Flask, request

load_dotenv()

TOKEN: Final = os.getenv("TOKEN")
if TOKEN is None:
    raise ValueError("TOKEN environment variable is not set.")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")

# Flask app
app_flask = Flask(__name__)

# Bot setup
bot_app = Application.builder().token(TOKEN).build()

#Commends
async def start_commend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is not None:
        await update.message.reply_text('start ဘူးကွာ')
        
async def help_commend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is not None:
        await update.message.reply_text('help ဘူးကွာ')
        
async def stop_commend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is not None:
        await update.message.reply_text('stop ဘူးကွာ')

#Handle responses
def handle_response(text: str) -> str:
    lowered = text.lower()
    if "hi" in lowered or "hello" in lowered:
        return "Lee hi"
    elif "lee" in lowered:
        return "lee lar"
    elif "ဟ" == lowered:
        return "လီးဟ"
    elif "လီး" in lowered:
        return "လီးလား"
    elif "fuck" in lowered:
        return "Fuck you too"
    return "သားသားချစ်တဲ့အားလုံး မဂ်လာပါ"


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

# Add handlers to bot
bot_app.add_handler(CommandHandler('start', start_commend))
bot_app.add_handler(CommandHandler('help', help_commend))
bot_app.add_handler(CommandHandler('stop', stop_commend))
bot_app.add_handler(MessageHandler(filters.TEXT, handle_message))
bot_app.add_error_handler(error_handle)

@app_flask.route('/')
def health_check():
    return 'Bot is running!'

@app_flask.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Get the update from Telegram
        update_data = request.get_json()
        
        # Create Update object
        update = Update.de_json(update_data, bot_app.bot)
        
        # Process the update synchronously
        asyncio.run(bot_app.process_update(update))
        
        return 'OK', 200
    except Exception as e:
        print(f'Error processing webhook: {e}')
        import traceback
        traceback.print_exc()
        return 'Error', 500

if __name__ == '__main__':
    # Initialize the bot
    async def init_bot():
        await bot_app.initialize()
        await bot_app.start()
    
    # Run the initialization
    asyncio.run(init_bot())
    
    # Get port from environment
    port = int(os.getenv('PORT', 8080))
    
    print(f'Bot webhook server running on port {port}')
    print('Bot is ready to receive webhooks!')
    
    # Run Flask app
    app_flask.run(host='0.0.0.0', port=port, debug=False)