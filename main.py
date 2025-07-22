from typing import Final
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
import asyncio
import json

load_dotenv()

TOKEN: Final = os.getenv("TOKEN")
if TOKEN is None:
    raise ValueError("TOKEN environment variable is not set.")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")

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

if __name__ == '__main__':
    import asyncio
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import json
    import threading
    
    # Get port from environment variable (Cloud Run requirement)
    port = int(os.getenv('PORT', 8080))
    
    # Set up the bot
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start_commend))
    app.add_handler(CommandHandler('help', help_commend))
    app.add_handler(CommandHandler('stop', stop_commend))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_error_handler(error_handle)

    # Global variable to store the event loop
    bot_loop = None
    
    def setup_bot():
        global bot_loop
        bot_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(bot_loop)
        
        async def init_bot():
            await app.initialize()
            await app.start()
        
        bot_loop.run_until_complete(init_bot())
        bot_loop.run_forever()
    
    # Start bot in separate thread
    bot_thread = threading.Thread(target=setup_bot, daemon=True)
    bot_thread.start()
    
    # Wait for bot to initialize
    import time
    time.sleep(2)
    
    class WebhookHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path == '/webhook':
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    update_data = json.loads(post_data.decode('utf-8'))
                    
                    # Process the update
                    update = Update.de_json(update_data, app.bot)
                    
                    # Schedule the update processing in the bot's event loop
                    if bot_loop and not bot_loop.is_closed():
                        asyncio.run_coroutine_threadsafe(app.process_update(update), bot_loop)
                    
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'OK')
                except Exception as e:
                    print(f'Error processing webhook: {e}')
                    import traceback
                    traceback.print_exc()
                    self.send_response(500)
                    self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()
        
        def do_GET(self):
            # Health check endpoint
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Bot is running!')
        
        def log_message(self, format, *args):
            # Suppress default logging
            pass
    
    # Start HTTP server for webhooks
    server = HTTPServer(('0.0.0.0', port), WebhookHandler)
    print(f'Bot webhook server running on port {port}')
    print('Bot is ready to receive webhooks!')
    
    # Keep the server running
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Shutting down...')
        if bot_loop:
            bot_loop.call_soon_threadsafe(bot_loop.stop)
        server.shutdown()