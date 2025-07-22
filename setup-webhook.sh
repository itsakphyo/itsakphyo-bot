#!/bin/bash

# Webhook Setup Script for GCP Cloud Run
# Run this AFTER your bot is deployed to Cloud Run

# Replace these with your actual values:
BOT_TOKEN="7854668878:AAFytTXx9HZLKIga9fyv-I1geX-oihH6rFM"
WEBHOOK_URL="https://YOUR-CLOUD-RUN-URL/webhook"  # Replace with your actual Cloud Run URL

echo "Setting up webhook for Telegram bot..."

# Set the webhook
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
     -H "Content-Type: application/json" \
     -d "{\"url\": \"${WEBHOOK_URL}\"}"

echo ""
echo "Webhook setup complete!"
echo ""
echo "To verify webhook status, run:"
echo "curl https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
