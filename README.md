# Itsakphyo - Telegram Bot

A production-ready Telegram bot with clean architecture and robust error handling.

 **Try the live bot**: [@itsakphyo_bot](https://t.me/itsakphyo_bot)

## Features

-  **Production Ready**: Structured codebase with proper error handling
-  **Docker Support**: Containerized deployment
-  **Monitoring**: Health checks and status monitoring
-  **Security**: Input validation and secure configuration
-  **Logging**: Comprehensive logging with rotation
-  **FastAPI**: High-performance async web framework
-  **Configurable**: Environment-based configuration

## Project Structure

```
itsakphyo-bot/             
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
├── static/               # Static files (if any)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── cloudbuild.yaml       # For GCP deployment
├── .env.example
├── .env.gcp.template     # For GCP deployment
├── start.bat             # Windows development script
├── start.sh              # Linux/Mac development script
└── main.py               # Entry point
```

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/itsakphyo/itsakphyo-bot
cd itsakphyo-bot
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your bot token and configuration
```

### 5. Run the Bot

**Option A: Using convenience scripts**
```bash
# Windows
.\start.bat

# Linux/Mac  
./start.sh
```

**Option B: Manual setup**
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

### Local Development Scripts

Use the provided convenience scripts for easy setup:

**Windows:**
```bash
.\start.bat
```

**Linux/Mac:**
```bash
./start.sh
```

These scripts automatically:
- Create virtual environment
- Install dependencies  
- Set up configuration files
- Start the application

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

- `/start` - Initialize the bot and show welcome message
- `/help` - Show help message with available commands
- `/stop` - Stop the bot gracefully

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Logs

Logs are stored in `logs/app.log` with automatic rotation.

## Architecture

### Core Components

- **TelegramService**: Handles Telegram bot operations and message processing
- **HTTPHandler**: Processes HTTP requests and webhook endpoints
- **Settings**: Manages configuration and environment variables

### Message Flow

1. **Telegram Webhook** → **HTTP Handler** → **Telegram Service**
2. **User Message** → **Command Processing** → **Response**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the bot locally using the provided scripts
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Aung Khant Phyo**
- Email: itsakphyo@gmail.com
- GitHub: [@itsakphyo](https://github.com/itsakphyo)

## Support

For issues and questions:
1. Check the logs in `logs/app.log`
2. Review the configuration in `.env`
3. Test bot functionality with basic commands
4. Open an issue on GitHub
