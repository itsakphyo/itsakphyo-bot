# Webhook Setup Script for GCP Cloud Run (PowerShell)
# Run this AFTER your bot is deployed to Cloud Run

# Replace these with your actual values:
$BOT_TOKEN = "7854668878:AAFytTXx9HZLKIga9fyv-I1geX-oihH6rFM"
$WEBHOOK_URL = "https://YOUR-CLOUD-RUN-URL/webhook"  # Replace with your actual Cloud Run URL

Write-Host "Setting up webhook for Telegram bot..." -ForegroundColor Green

# Prepare the request body
$body = @{
    url = $WEBHOOK_URL
} | ConvertTo-Json

# Set the webhook
try {
    $response = Invoke-RestMethod -Uri "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" `
                                  -Method Post `
                                  -Body $body `
                                  -ContentType "application/json"
    
    Write-Host "Webhook setup response:" -ForegroundColor Yellow
    $response | ConvertTo-Json -Depth 3
    
    if ($response.ok) {
        Write-Host "Webhook setup successful!" -ForegroundColor Green
    } else {
        Write-Host "Webhook setup failed: $($response.description)" -ForegroundColor Red
    }
} catch {
    Write-Host "Error setting up webhook: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "To verify webhook status, run:" -ForegroundColor Cyan
Write-Host "Invoke-RestMethod -Uri 'https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo'" -ForegroundColor Cyan
