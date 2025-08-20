# Google Cloud Platform Deployment Guide

This guide will help you deploy your Telegram bot to Google Cloud Platform without requiring a domain.

## Prerequisites

1. **Google Cloud Account**: Create a free account at [Google Cloud Console](https://console.cloud.google.com/)
2. **Google Cloud CLI**: Install from [here](https://cloud.google.com/sdk/docs/install)
3. **Docker**: Install from [here](https://docs.docker.com/get-docker/)
4. **A Google Cloud Project**: Create one in the Google Cloud Console

## Quick Setup

### 1. Install Google Cloud CLI

**Windows:**
```powershell
# Download and run the installer from: https://cloud.google.com/sdk/docs/install-sdk
```

**Linux/Mac:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### 2. Authenticate and Set Project

```bash
# Login to Google Cloud
gcloud auth login

# Set your project (replace YOUR_PROJECT_ID with your actual project ID)
gcloud config set project YOUR_PROJECT_ID

# Verify your setup
gcloud config list
```

### 3. Prepare Environment Variables

Copy the GCP environment template:
```bash
cp .env.gcp .env.gcp.local
```

Edit `.env.gcp.local` with your actual values:
```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
TELEGRAM_BOT_USERNAME=your_bot_username

# Server Configuration (Google Cloud Run uses PORT environment variable)
PORT=8080
HOST=0.0.0.0
ENVIRONMENT=production

# Logging
LOG_LEVEL=INFO
```

### 4. Deploy to Google Cloud Run

**Option A: Using the automated script (Recommended)**

For Windows PowerShell:
```powershell
.\deploy-gcp.ps1
```

For Linux/Mac:
```bash
chmod +x deploy-gcp.sh
./deploy-gcp.sh
```

**Option B: Manual deployment**

```bash
# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push the image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/itsakphyo-bot

# Deploy to Cloud Run
gcloud run deploy itsakphyo-bot \
  --image gcr.io/YOUR_PROJECT_ID/itsakphyo-bot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars TELEGRAM_BOT_TOKEN=your_token,TELEGRAM_BOT_USERNAME=your_username,ENVIRONMENT=production
```

## Configuration Details

### Environment Variables for GCP

Your `.env.gcp` file should contain:

```env
# Required: Your Telegram bot token from @BotFather
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Required: Your bot username (without @)
TELEGRAM_BOT_USERNAME=your_bot_username

# Google Cloud Run Configuration
PORT=8080
HOST=0.0.0.0
ENVIRONMENT=production

# Optional: Logging configuration
LOG_LEVEL=INFO
```

### Google Cloud Run Specifications

- **Memory**: 512Mi (can be increased if needed)
- **CPU**: 1 vCPU
- **Port**: 8080 (required by Google Cloud Run)
- **Scaling**: 0 to 10 instances (auto-scaling)
- **Timeout**: 900 seconds (15 minutes)
- **Authentication**: Allow unauthenticated requests

## Setting Up Your Telegram Webhook

After deployment, you'll get a service URL like:
```
https://itsakphyo-bot-abc123-uc.a.run.app
```

### Set the Webhook URL

1. **Option A: Use curl**
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
        -H "Content-Type: application/json" \
        -d '{"url": "https://your-service-url/webhook"}'
   ```

2. **Option B: Use the bot's webhook endpoint**
   ```bash
   curl -X POST "https://your-service-url/webhook/set"
   ```

## Testing Your Deployment

### 1. Health Check
```bash
curl https://your-service-url/health
```

### 2. Telegram Bot
Send `/start` or `/help` to your bot on Telegram.

## Monitoring and Logs

### View Logs
```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=itsakphyo-bot" --limit 50

# Stream logs in real-time
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=itsakphyo-bot"
```

### Monitoring Dashboard
Go to [Google Cloud Console](https://console.cloud.google.com/) → Cloud Run → Your Service → Logs/Metrics

## Cost Optimization

Google Cloud Run pricing (as of 2024):
- **Free Tier**: 180,000 vCPU-seconds, 360,000 GiB-seconds, 2 million requests per month
- **Paid Usage**: ~$0.000024 per vCPU-second, ~$0.0000025 per GiB-second

### Cost Optimization Tips:
1. **Set min-instances to 0** for auto-scaling to zero
2. **Use appropriate memory allocation** (512Mi is usually sufficient)
3. **Monitor usage** in Google Cloud Console
4. **Set up billing alerts** to avoid unexpected charges

## Troubleshooting

### Common Issues

1. **Build Fails**
   ```bash
   # Check build logs
   gcloud builds log --stream
   ```

2. **Service Won't Start**
   ```bash
   # Check service logs
   gcloud run services logs read itsakphyo-bot --region us-central1
   ```

3. **Webhook Not Working**
   - Verify webhook URL is set correctly
   - Check that service is publicly accessible
   - Ensure bot token is correct

4. **Memory Issues**
   ```bash
   # Increase memory allocation
   gcloud run services update itsakphyo-bot --memory 1Gi --region us-central1
   ```

### Debug Commands

```bash
# Check service status
gcloud run services describe itsakphyo-bot --region us-central1

# List all revisions
gcloud run revisions list --service itsakphyo-bot --region us-central1

# Get service URL
gcloud run services describe itsakphyo-bot --region us-central1 --format 'value(status.url)'
```

## Security Best Practices

1. **Environment Variables**: Never commit real tokens to version control
2. **IAM Roles**: Use least privilege principle
3. **Network Security**: Google Cloud Run provides HTTPS by default
4. **Monitoring**: Set up alerts for unusual activity

## Updating Your Deployment

To update your service:

```bash
# Rebuild and redeploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/itsakphyo-bot
gcloud run deploy itsakphyo-bot --image gcr.io/YOUR_PROJECT_ID/itsakphyo-bot --region us-central1
```

Or simply run the deployment script again:
```bash
./deploy-gcp.sh  # Linux/Mac
.\deploy-gcp.ps1 # Windows
```

## Support

If you encounter issues:

1. Check the [Google Cloud Run documentation](https://cloud.google.com/run/docs)
2. Review the service logs in Google Cloud Console
3. Verify your environment variables are set correctly

## File Structure for GCP Deployment

```
├── app/                          # Application code
├── .env.gcp                      # GCP environment template
├── .env.gcp.local               # Your actual environment (don't commit)
├── Dockerfile                    # Optimized for Google Cloud Run
├── cloudbuild.yaml              # Google Cloud Build configuration
├── deploy-gcp.sh                # Linux/Mac deployment script
├── deploy-gcp.ps1               # Windows PowerShell deployment script
├── requirements.txt             # Python dependencies
└── README-GCP.md               # This file
```

## Next Steps

After successful deployment:

1. **Monitor Performance**: Use Google Cloud Console monitoring
2. **Set Up Alerts**: Configure billing and performance alerts
3. **Scale as Needed**: Adjust memory and CPU based on usage
4. **Backup Configuration**: Save your environment variables securely
5. **CI/CD**: Consider setting up automated deployments with Google Cloud Build

Your Telegram bot is now running on Google Cloud Platform without requiring a domain! 🚀
