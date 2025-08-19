#!/bin/bash

# Google Cloud Platform Deployment Script
# This script helps deploy the Telegram WebSocket bot to Google Cloud Run

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Telegram WebSocket Bot - GCP Deployment ===${NC}"

# Check if required tools are installed
check_requirements() {
    echo -e "${YELLOW}Checking requirements...${NC}"
    
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}Error: Google Cloud CLI (gcloud) is not installed.${NC}"
        echo "Please install it from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed.${NC}"
        echo "Please install Docker from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All requirements met${NC}"
}

# Set up project variables
setup_project() {
    echo -e "${YELLOW}Setting up project variables...${NC}"
    
    # Get current project
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
    
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}Error: No Google Cloud project is set.${NC}"
        echo "Please set your project with: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Using project: $PROJECT_ID${NC}"
    
    # Set variables
    SERVICE_NAME="itsakphyo-bot"
    REGION="us-central1"  # Change this to your preferred region
    IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
    
    echo -e "${BLUE}Service Name: $SERVICE_NAME${NC}"
    echo -e "${BLUE}Region: $REGION${NC}"
    echo -e "${BLUE}Image: $IMAGE_NAME${NC}"
}

# Enable required APIs
enable_apis() {
    echo -e "${YELLOW}Enabling required Google Cloud APIs...${NC}"
    
    gcloud services enable run.googleapis.com
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    
    echo -e "${GREEN}✓ APIs enabled${NC}"
}

# Build and push Docker image
build_and_push() {
    echo -e "${YELLOW}Building and pushing Docker image...${NC}"
    
    # Build the image
    docker build -t $IMAGE_NAME .
    
    # Configure Docker to use gcloud as credential helper
    gcloud auth configure-docker
    
    # Push the image
    docker push $IMAGE_NAME
    
    echo -e "${GREEN}✓ Image built and pushed${NC}"
}

# Deploy to Cloud Run
deploy_to_cloud_run() {
    echo -e "${YELLOW}Deploying to Google Cloud Run...${NC}"
    
    # Check if .env.gcp exists
    if [ ! -f ".env.gcp" ]; then
        echo -e "${RED}Error: .env.gcp file not found.${NC}"
        echo "Please create .env.gcp with your environment variables."
        exit 1
    fi
    
    # Read environment variables from .env.gcp
    ENV_VARS=""
    while IFS= read -r line; do
        if [[ $line == *"="* ]] && [[ $line != "#"* ]]; then
            ENV_VARS="$ENV_VARS--set-env-vars $line "
        fi
    done < .env.gcp
    
    # Deploy to Cloud Run
    gcloud run deploy $SERVICE_NAME \
        --image $IMAGE_NAME \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --port 8080 \
        --memory 512Mi \
        --cpu 1 \
        --min-instances 0 \
        --max-instances 10 \
        --timeout 900 \
        $ENV_VARS
    
    echo -e "${GREEN}✓ Deployment completed${NC}"
}

# Get service URL
get_service_url() {
    echo -e "${YELLOW}Getting service URL...${NC}"
    
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')
    
    echo -e "${GREEN}✓ Service deployed successfully!${NC}"
    echo -e "${BLUE}Service URL: $SERVICE_URL${NC}"
    echo -e "${BLUE}Dashboard: $SERVICE_URL/dashboard${NC}"
    echo -e "${BLUE}Health Check: $SERVICE_URL/health${NC}"
    echo -e "${BLUE}WebSocket Test: $SERVICE_URL/ws/test${NC}"
}

# Main deployment function
main() {
    echo -e "${BLUE}Starting deployment process...${NC}"
    
    check_requirements
    setup_project
    enable_apis
    build_and_push
    deploy_to_cloud_run
    get_service_url
    
    echo -e "${GREEN}=== Deployment completed successfully! ===${NC}"
    echo -e "${YELLOW}Note: Make sure to update your Telegram webhook URL to: $SERVICE_URL/webhook${NC}"
}

# Run main function
main "$@"
