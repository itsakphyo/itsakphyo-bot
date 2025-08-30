#!/usr/bin/env python3
"""
Deployment script for the Aung Khant Phyo Bot.
Uses the same deployment flow as update_documents.py but without document updates.
"""
import asyncio
import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BotDeployer:
    """Handle deployment for the RAG system."""
    
    def __init__(self):
        pass
    
    def deploy_to_gcp(self):
        """Deploy the bot to Google Cloud Run."""
        print(f"\n🚀 Starting deployment to Google Cloud Run...")
        
        # Check if required environment variables are set
        required_vars = {
            'GOOGLE_CLOUD_PROJECT_ID': os.getenv('GOOGLE_CLOUD_PROJECT_ID'),
            'TOKEN': os.getenv('TOKEN'),
            'BOT_USERNAME': os.getenv('BOT_USERNAME'),
            'GOOGLE_DRIVE_FOLDER_ID': os.getenv('GOOGLE_DRIVE_FOLDER_ID'),
            'GOOGLE_CLOUD_REGION': os.getenv('GOOGLE_CLOUD_REGION'),
            'GOOGLE_CLOUD_RUN_REGION': os.getenv('GOOGLE_CLOUD_RUN_REGION')
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            print(f"❌ Missing environment variables for deployment: {', '.join(missing_vars)}")
            print(f"Please check your .env file.")
            return False
        
        try:
            # Build and deploy using gcloud
            project_id = required_vars['GOOGLE_CLOUD_PROJECT_ID']
            region = required_vars['GOOGLE_CLOUD_RUN_REGION']  # Use separate region for Cloud Run
            service_name = "itsakphyo-bot"
            
            # Check if service already exists
            print(f"🔍 Checking if service exists...")
            check_cmd = f'gcloud run services describe {service_name} --region={region} --project={project_id} --quiet'
            check_result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            
            service_exists = check_result.returncode == 0
            if service_exists:
                print(f"✅ Found existing service - will update it")
            else:
                print(f"ℹ️  No existing service - will create new one")
            
            print(f"📦 Building Docker image...")
            build_cmd = f'gcloud builds submit --tag gcr.io/{project_id}/{service_name}:latest . --quiet'
            
            result = subprocess.run(build_cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Docker build failed:")
                print(result.stderr)
                return False
            
            print(f"✅ Docker image built successfully!")
            
            if service_exists:
                print(f"🔄 Updating existing Cloud Run service...")
            else:
                print(f"🚀 Creating new Cloud Run service...")
                
            deploy_cmd = f'''gcloud run deploy {service_name} \
                --image gcr.io/{project_id}/{service_name}:latest \
                --platform managed \
                --region {region} \
                --project {project_id} \
                --allow-unauthenticated \
                --set-env-vars TOKEN={required_vars['TOKEN']} \
                --set-env-vars BOT_USERNAME={required_vars['BOT_USERNAME']} \
                --set-env-vars GOOGLE_CLOUD_PROJECT_ID={project_id} \
                --set-env-vars GOOGLE_DRIVE_FOLDER_ID={required_vars['GOOGLE_DRIVE_FOLDER_ID']} \
                --set-env-vars GOOGLE_CLOUD_REGION={required_vars['GOOGLE_CLOUD_REGION']} \
                --set-env-vars GOOGLE_CLOUD_RUN_REGION={required_vars['GOOGLE_CLOUD_RUN_REGION']} \
                --memory 1Gi \
                --cpu 1 \
                --timeout 900 \
                --concurrency 100 \
                --max-instances 10 \
                --min-instances 1 \
                --quiet'''
            
            result = subprocess.run(deploy_cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Deployment failed:")
                print(result.stderr)
                return False
            
            if service_exists:
                print(f"✅ Service updated successfully!")
            else:
                print(f"✅ Service created successfully!")
            
            # Extract service URL from deployment output
            if "Service URL:" in result.stdout:
                service_url = result.stdout.split("Service URL: ")[1].split("\n")[0].strip()
                print(f"🌐 Service URL: {service_url}")
                
                # Set webhook
                print(f"🔗 Setting Telegram webhook...")
                webhook_url = f"{service_url}/webhook"
                webhook_cmd = f'curl -X POST "https://api.telegram.org/bot{required_vars["TOKEN"]}/setWebhook" -d "url={webhook_url}"'
                
                webhook_result = subprocess.run(webhook_cmd, shell=True, capture_output=True, text=True)
                if webhook_result.returncode == 0:
                    print(f"✅ Webhook set successfully!")
                    print(f"🎯 Webhook URL: {webhook_url}")
                else:
                    print(f"⚠️  Warning: Could not set webhook automatically")
                    print(f"Please set it manually: {webhook_url}")
            else:
                # If URL not found in stdout, try to get it manually
                print(f"🔍 Getting service URL...")
                url_cmd = f'gcloud run services describe {service_name} --region={region} --project={project_id} --format="value(status.url)"'
                url_result = subprocess.run(url_cmd, shell=True, capture_output=True, text=True)
                
                if url_result.returncode == 0 and url_result.stdout.strip():
                    service_url = url_result.stdout.strip()
                    print(f"🌐 Service URL: {service_url}")
                    
                    # Set webhook
                    print(f"🔗 Setting Telegram webhook...")
                    webhook_url = f"{service_url}/webhook"
                    webhook_cmd = f'curl -X POST "https://api.telegram.org/bot{required_vars["TOKEN"]}/setWebhook" -d "url={webhook_url}"'
                    
                    webhook_result = subprocess.run(webhook_cmd, shell=True, capture_output=True, text=True)
                    if webhook_result.returncode == 0:
                        print(f"✅ Webhook set successfully!")
                        print(f"🎯 Webhook URL: {webhook_url}")
                    else:
                        print(f"⚠️  Warning: Could not set webhook automatically")
                        print(f"Please set it manually: {webhook_url}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Deployment command failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Deployment error: {e}")
            return False

async def main():
    """Main function to run the deployment process."""
    print("🚀 Aung Khant Phyo Bot - Deployer")
    print("=" * 60)
    
    # Check environment
    required_vars = ['GOOGLE_CLOUD_PROJECT_ID', 'GOOGLE_DRIVE_FOLDER_ID', 'GOOGLE_CLOUD_REGION', 'GOOGLE_CLOUD_RUN_REGION']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print(f"Please check your .env file.")
        return 1
    
    # Create deployer and run
    deployer = BotDeployer()
    
    try:
        # Deploy to GCP
        print(f"\n" + "=" * 60)
        deploy_response = input("Would you like to deploy to Google Cloud Run? (y/n): ").lower().strip()
        if deploy_response in ['y', 'yes']:
            deployment_success = deployer.deploy_to_gcp()
            if deployment_success:
                print(f"\n🎉 Complete! Your bot is deployed to production!")
            else:
                print(f"\n⚠️  Deployment failed.")
                print(f"You can deploy manually using: gcloud run deploy")
                return 1
        else:
            print(f"\n✅ Deployment cancelled by user.")
        
        print(f"\n✅ All done!")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Process interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
