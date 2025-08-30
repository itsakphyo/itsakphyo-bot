#!/usr/bin/env python3
"""
Auto-update and deployment script for when documents are edited in Google Drive.
Run this script after editing your resume or documents to refresh the RAG corpus A                print(f"🔄 Updating existing service...")
            else:
                print(f"🚀 Creating new service...")deploy to GCP.
"""
import asyncio
import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DocumentUpdaterAndDeployer:
    """Handle document updates and deployment for the RAG system."""
    
    def __init__(self):
        self.rag_service = None
        
    async def update_documents(self):
        """Update the RAG corpus with latest documents from Google Drive."""
        print("🔄 Starting document update process...")
        
        try:
            # Import required modules
            from app.services.rag_service import rag_service
            from vertexai.preview import rag
            self.rag_service = rag_service
            print("✅ Modules loaded successfully")
        except ImportError as e:
            print(f"❌ Failed to import modules: {e}")
            return False
        
        # Initialize RAG service
        print("\n🚀 Initializing RAG service...")
        success = await self.rag_service.initialize()
        
        if not success:
            print("❌ RAG service initialization failed")
            return False
            
        print("✅ RAG service initialized successfully!")
        
        # Check current corpus
        if not self.rag_service.rag_corpus or not hasattr(self.rag_service.rag_corpus, 'name'):
            print("❌ RAG corpus not properly initialized")
            return False
            
        corpus_name = self.rag_service.rag_corpus.name
        print(f"📊 Working with corpus: {corpus_name}")
        
        # Get current file count
        try:
            if corpus_name:
                current_files = rag.list_files(corpus_name=corpus_name)
                current_count = len(current_files.rag_files) if current_files.rag_files else 0
                print(f"📁 Current files in corpus: {current_count}")
                
                if current_count > 0:
                    print("🗑️  Removing old files...")
                    for file in current_files.rag_files:
                        try:
                            rag.delete_file(name=file.name)
                            print(f"   ✅ Deleted: {file.display_name}")
                        except Exception as e:
                            print(f"   ⚠️  Could not delete {file.display_name}: {e}")
            else:
                print("❌ Corpus name is None")
                return False
                        
        except Exception as e:
            print(f"⚠️  Could not check existing files: {e}")
        
        # Import fresh files from Google Drive
        print(f"\n📥 Importing fresh files from Google Drive...")
        try:
            drive_folder_id = self.rag_service.drive_folder_id
            if corpus_name:
                operation = rag.import_files(
                    corpus_name=corpus_name,
                    paths=[f"https://drive.google.com/drive/folders/{drive_folder_id}"],
                    chunk_size=512,
                    chunk_overlap=50,
                )
                print(f"✅ Import operation completed!")
                print(f"📋 Result: {operation}")
                
                # Wait for processing
                print(f"\n⏳ Waiting for files to be processed...")
                await asyncio.sleep(15)
                
                # Check new file count
                try:
                    new_files = rag.list_files(corpus_name=corpus_name)
                    new_count = len(new_files.rag_files) if new_files.rag_files else 0
                    print(f"📁 Updated files in corpus: {new_count}")
                    
                    if new_count > 0:
                        print(f"🎉 Successfully updated! New files:")
                        for i, file in enumerate(new_files.rag_files):
                            print(f"   {i+1}. {file.display_name}")
                    else:
                        print(f"⚠️  No files found after update. Please check:")
                        print(f"   1. Documents exist in Google Drive folder")
                        print(f"   2. Files are in supported formats (PDF, DOCX, TXT)")
                        print(f"   3. Service account has proper permissions")
                        
                except Exception as e:
                    print(f"❌ Error checking updated files: {e}")
            else:
                print("❌ Corpus name is None for import")
                return False
                
        except Exception as e:
            print(f"❌ Error importing files: {e}")
            return False
            
        print(f"\n✅ Document update process completed!")
        return True
    
    async def test_responses(self):
        """Test the bot responses after update."""
        if not self.rag_service:
            print("❌ RAG service not initialized")
            return
            
        print(f"\n🧪 Testing updated responses...")
        
        test_queries = [
            "Hello",
            "Who is Aung Khant Phyo?",
            "What are his main skills?"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: {query}")
            try:
                response = await self.rag_service.generate_response(query)
                # Truncate long responses for display
                display_response = response[:200] + "..." if len(response) > 200 else response
                print(f"🤖 Response: {display_response}")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def deploy_to_gcp(self):
        """Deploy the updated bot to Google Cloud Run."""
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
                print(f"� Updating existing Cloud Run service...")
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
    """Main function to run the document update and deployment process."""
    print("🚀 Aung Khant Phyo Bot - Document Updater & Deployer")
    print("=" * 60)
    
    # Check environment
    required_vars = ['GOOGLE_CLOUD_PROJECT_ID', 'GOOGLE_DRIVE_FOLDER_ID', 'GOOGLE_CLOUD_REGION', 'GOOGLE_CLOUD_RUN_REGION']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print(f"Please check your .env file.")
        return
    
    # Create updater and run
    updater = DocumentUpdaterAndDeployer()
    
    try:
        # Step 1: Update documents
        success = await updater.update_documents()
        
        if not success:
            print("❌ Document update failed. Skipping deployment.")
            return 1
        
        # Step 2: Test responses (optional)
        print(f"\n" + "=" * 60)
        test_response = input("Would you like to test the updated responses? (y/n): ").lower().strip()
        if test_response in ['y', 'yes']:
            await updater.test_responses()
        
        # Step 3: Deploy to GCP
        print(f"\n" + "=" * 60)
        deploy_response = input("Would you like to deploy to Google Cloud Run? (y/n): ").lower().strip()
        if deploy_response in ['y', 'yes']:
            deployment_success = updater.deploy_to_gcp()
            if deployment_success:
                print(f"\n🎉 Complete! Your bot is updated and deployed to production!")
            else:
                print(f"\n⚠️  Document update succeeded, but deployment failed.")
                print(f"You can deploy manually using: gcloud run deploy")
        else:
            print(f"\n✅ Documents updated! Deploy manually when ready.")
        
        print(f"\n✅ All done! Your bot knowledge base is updated.")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
