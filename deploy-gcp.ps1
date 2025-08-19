# Google Cloud Platform Deployment Script for Windows PowerShell
# This script helps deploy the Telegram WebSocket bot to Google Cloud Run

param(
    [string]$ProjectId = "",
    [string]$Region = "us-central1",
    [string]$ServiceName = "itsakphyo-bot"
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

Write-Host "=== Telegram WebSocket Bot - GCP Deployment ===" -ForegroundColor $Blue

# Check if required tools are installed
function Check-Requirements {
    Write-Host "Checking requirements..." -ForegroundColor $Yellow
    
    try {
        $null = Get-Command gcloud -ErrorAction Stop
        Write-Host "✓ Google Cloud CLI found" -ForegroundColor $Green
    }
    catch {
        Write-Host "Error: Google Cloud CLI (gcloud) is not installed." -ForegroundColor $Red
        Write-Host "Please install it from: https://cloud.google.com/sdk/docs/install"
        exit 1
    }
    
    try {
        $null = Get-Command docker -ErrorAction Stop
        Write-Host "✓ Docker found" -ForegroundColor $Green
    }
    catch {
        Write-Host "Error: Docker is not installed." -ForegroundColor $Red
        Write-Host "Please install Docker from: https://docs.docker.com/get-docker/"
        exit 1
    }
    
    Write-Host "✓ All requirements met" -ForegroundColor $Green
}

# Set up project variables
function Setup-Project {
    Write-Host "Setting up project variables..." -ForegroundColor $Yellow
    
    if (-not $ProjectId) {
        $currentProject = gcloud config get-value project 2>$null
        if (-not $currentProject) {
            Write-Host "Error: No Google Cloud project is set." -ForegroundColor $Red
            Write-Host "Please set your project with: gcloud config set project YOUR_PROJECT_ID"
            exit 1
        }
        $script:ProjectId = $currentProject
    }
    
    Write-Host "✓ Using project: $ProjectId" -ForegroundColor $Green
    
    $script:ImageName = "gcr.io/$ProjectId/$ServiceName"
    
    Write-Host "Service Name: $ServiceName" -ForegroundColor $Blue
    Write-Host "Region: $Region" -ForegroundColor $Blue
    Write-Host "Image: $ImageName" -ForegroundColor $Blue
}

# Enable required APIs
function Enable-APIs {
    Write-Host "Enabling required Google Cloud APIs..." -ForegroundColor $Yellow
    
    gcloud services enable run.googleapis.com
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    
    Write-Host "✓ APIs enabled" -ForegroundColor $Green
}

# Build and push Docker image
function Build-AndPush {
    Write-Host "Building and pushing Docker image..." -ForegroundColor $Yellow
    
    # Build the image
    docker build -t $ImageName .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Docker build failed" -ForegroundColor $Red
        exit 1
    }
    
    # Configure Docker to use gcloud as credential helper
    gcloud auth configure-docker
    
    # Push the image
    docker push $ImageName
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Docker push failed" -ForegroundColor $Red
        exit 1
    }
    
    Write-Host "✓ Image built and pushed" -ForegroundColor $Green
}

# Deploy to Cloud Run
function Deploy-ToCloudRun {
    Write-Host "Deploying to Google Cloud Run..." -ForegroundColor $Yellow
    
    # Check if .env.gcp exists
    if (-not (Test-Path ".env.gcp")) {
        Write-Host "Error: .env.gcp file not found." -ForegroundColor $Red
        Write-Host "Please create .env.gcp with your environment variables."
        exit 1
    }
    
    # Read environment variables from .env.gcp
    $envVars = @()
    Get-Content ".env.gcp" | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $envVars += "--set-env-vars"
            $envVars += $line
        }
    }
    
    # Deploy to Cloud Run
    $deployArgs = @(
        "run", "deploy", $ServiceName,
        "--image", $ImageName,
        "--platform", "managed",
        "--region", $Region,
        "--allow-unauthenticated",
        "--port", "8080",
        "--memory", "512Mi",
        "--cpu", "1",
        "--min-instances", "0",
        "--max-instances", "10",
        "--timeout", "900"
    )
    
    if ($envVars.Count -gt 0) {
        $deployArgs += $envVars
    }
    
    & gcloud $deployArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Cloud Run deployment failed" -ForegroundColor $Red
        exit 1
    }
    
    Write-Host "✓ Deployment completed" -ForegroundColor $Green
}

# Get service URL
function Get-ServiceUrl {
    Write-Host "Getting service URL..." -ForegroundColor $Yellow
    
    $serviceUrl = gcloud run services describe $ServiceName --platform managed --region $Region --format "value(status.url)"
    
    Write-Host "✓ Service deployed successfully!" -ForegroundColor $Green
    Write-Host "Service URL: $serviceUrl" -ForegroundColor $Blue
    Write-Host "Dashboard: $serviceUrl/dashboard" -ForegroundColor $Blue
    Write-Host "Health Check: $serviceUrl/health" -ForegroundColor $Blue
    Write-Host "WebSocket Test: $serviceUrl/ws/test" -ForegroundColor $Blue
    
    return $serviceUrl
}

# Main deployment function
function Main {
    Write-Host "Starting deployment process..." -ForegroundColor $Blue
    
    try {
        Check-Requirements
        Setup-Project
        Enable-APIs
        Build-AndPush
        Deploy-ToCloudRun
        $serviceUrl = Get-ServiceUrl
        
        Write-Host "=== Deployment completed successfully! ===" -ForegroundColor $Green
        Write-Host "Note: Make sure to update your Telegram webhook URL to: $serviceUrl/webhook" -ForegroundColor $Yellow
    }
    catch {
        Write-Host "Error during deployment: $($_.Exception.Message)" -ForegroundColor $Red
        exit 1
    }
}

# Run main function
Main
