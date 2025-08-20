# Itsakphyo Bot - Production-Ready Telegram Bot

A production-ready Telegram bot with clean architecture and robust error handling.

## Features

-  **Production Ready**: Structured codebase with proper error handling
- 🐳 **Docker Support**: Containerized deployment
- 📊 **Monitoring**: Health checks and status monitoring
- 🔒 **Security**: Input validation and secure configuration
- 📝 **Logging**: Comprehensive logging with rotation
- ⚡ **FastAPI**: High-performance async web framework
- 🔧 **Configurable**: Environment-based configuration

## Project Structure

```
itsakphyo-bot/                    # You can rename this to any name you prefer
├── app/
│   ├── handlers/          # Request handlers
│   │   └── http_handler.py
│   ├── services/          # Business logic
│   │   └── telegram_service.py
│   ├── models/            # Data models
│   │   └── schemas.py
│   ├── utils/             # Utility functions
│   │   └── helpers.py
│   └── main.py            # FastAPI application
├── config/                # Configuration
│   ├── settings.py
│   └── logging.py
├── logs/                  # Log files
├── tests/                 # Test files
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── cloudbuild.yaml       # For GCP deployment
├── .env.example
├── .env.gcp.template     # For GCP deployment
└── main.py               # Entry point
```

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd itsakphyo-bot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your bot token and configuration
```

### 4. Run the Bot

```bash
python main.py
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Bot Configuration
TOKEN=your_telegram_bot_token_here
BOT_USERNAME=@your_bot_username_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
```

### Getting Bot Token

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Copy the token to your `.env` file

## API Endpoints

### HTTP Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /webhook` - Telegram webhook
- `POST /webhook/set` - Set webhook URL
- `DELETE /webhook` - Delete webhook

## Docker Deployment

### Build and Run

```bash
# Build image
docker build -t itsakphyo-bot .

# Run container
docker run -d \
  --name itsakphyo-bot \
  -p 8000:8000 \
  --env-file .env \
  itsakphyo-bot
```

### Using Docker Compose

```bash
# Build and run (you can change the service name in docker-compose.yml)
docker-compose up -d
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
python tests/test_telegram.py
```

### Code Formatting

```bash
# Install development dependencies
pip install black flake8 mypy

# Format code
black .

# Check code style
flake8 .

# Type checking
mypy .
```

## Production Setup

### 1. Set Webhook

For production, set up webhook instead of polling:

```bash
curl -X POST "http://localhost:8000/webhook/set?webhook_url=https://yourdomain.com/webhook"
```

### 2. Environment Configuration

```env
ENVIRONMENT=production
DEBUG=False
WEBHOOK_URL=https://yourdomain.com
```

### 3. Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Bot Commands

- `/start` - Initialize the bot
- `/help` - Show help message
- `/status` - Show bot and connection status
- `/stop` - Stop the bot

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Connection Stats

```bash
curl http://localhost:8000/stats
```

### Logs

Logs are stored in `logs/app.log` with automatic rotation.

## Architecture

### Core Components

- **TelegramService**: Handles Telegram bot operations and message processing
- **HTTPHandler**: Processes HTTP requests and webhook endpoints
- **BotStats**: Manages bot statistics and health monitoring

### Message Flow

1. **Telegram Webhook** → **HTTP Handler** → **Telegram Service**
2. **User Message** → **Command Processing** → **Response**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if needed
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the logs in `logs/app.log`
2. Review the configuration in `.env`
3. Test bot functionality with basic commands
4. Open an issue on GitHub
