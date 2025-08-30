"""
Google Cloud RAG Engine service for intelligent responses.
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from config.settings import settings
import os

logger = logging.getLogger(__name__)

try:
    import vertexai
    from vertexai.preview import rag
    from vertexai.preview.generative_models import GenerativeModel, Tool
    VERTEXAI_AVAILABLE = True
except ImportError:
    logger.warning("Google Cloud AI Platform not available. Install with: pip install google-cloud-aiplatform")
    VERTEXAI_AVAILABLE = False


class RAGService:
    """Service for handling RAG-based intelligent responses using Google Cloud."""
    
    def __init__(self):
        self.project_id: Optional[str] = None
        self.region: Optional[str] = None
        self.drive_folder_id: Optional[str] = None
        self.embedding_model: str = "publishers/google/models/text-embedding-004"
        self.llm_model: str = "gemini-1.5-flash-002"
        self.rag_corpus = None
        self.llm = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize the RAG service with Google Cloud credentials."""
        if not VERTEXAI_AVAILABLE:
            logger.warning("VertexAI not available, RAG service disabled")
            return False
            
        try:
            # Get configuration from environment variables
            self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
            self.region = os.getenv("GOOGLE_CLOUD_REGION", "europe-west3")
            self.drive_folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
            
            # Check if required credentials are available
            if not self.project_id:
                logger.warning("GOOGLE_CLOUD_PROJECT_ID not set, RAG service disabled")
                return False
                
            if not self.drive_folder_id:
                logger.warning("GOOGLE_DRIVE_FOLDER_ID not set, RAG service disabled")
                return False
            
            # Initialize Vertex AI
            vertexai.init(project=self.project_id, location=self.region) # type: ignore
            
            # Create embedding model configuration
            embedding_model_config = rag.EmbeddingModelConfig( # type: ignore
                publisher_model=self.embedding_model
            )
            
            # Check if RAG corpus already exists or create new one
            await self._setup_rag_corpus(embedding_model_config)
            
            # Setup the LLM with RAG tool
            await self._setup_llm()
            
            self.initialized = True
            logger.info("RAG service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            return False
    
    async def _setup_rag_corpus(self, embedding_model_config):
        """Setup or reuse existing RAG corpus."""
        if not VERTEXAI_AVAILABLE:
            return
            
        try:
            # List existing corpora to see if we already have one
            existing_corpora = list(rag.list_corpora()) # type: ignore
            
            # Look for existing corpus
            for corpus in existing_corpora:
                if corpus.display_name == "telegram-bot-rag-corpus":
                    self.rag_corpus = corpus
                    logger.info("Using existing RAG corpus")
                    return
            
            # Create new corpus if none exists
            logger.info("Creating new RAG corpus...")
            self.rag_corpus = rag.create_corpus( # type: ignore
                display_name="telegram-bot-rag-corpus",
                embedding_model_config=embedding_model_config
            )
            
            # Import files from Google Drive
            if self.rag_corpus and hasattr(self.rag_corpus, 'name') and self.rag_corpus.name:
                logger.info("Importing files from Google Drive...")
                rag.import_files( # type: ignore
                    corpus_name=self.rag_corpus.name,
                    paths=[f"https://drive.google.com/drive/folders/{self.drive_folder_id}"],
                    chunk_size=512,
                    chunk_overlap=50,
                )
                logger.info("Files imported successfully")
            
        except Exception as e:
            logger.error(f"Error setting up RAG corpus: {e}")
            raise
    
    async def _setup_llm(self):
        """Setup the LLM with RAG retrieval tool."""
        if not VERTEXAI_AVAILABLE or not self.rag_corpus:
            return
            
        try:
            # Create RAG store
            if hasattr(self.rag_corpus, 'name') and self.rag_corpus.name:
                rag_store = rag.VertexRagStore( # type: ignore
                    rag_corpora=[self.rag_corpus.name],
                    similarity_top_k=5,  # Reduced for faster responses
                    vector_distance_threshold=0.6,  # Adjusted threshold
                )
                
                # Create RAG retrieval tool
                rag_retrieval_tool = Tool.from_retrieval( # type: ignore
                    retrieval=rag.Retrieval(source=rag_store) # type: ignore
                )
                
                # Initialize LLM with RAG tool
                self.llm = GenerativeModel( # type: ignore
                    self.llm_model,
                    tools=[rag_retrieval_tool],
                )
                
                logger.info("LLM with RAG tool setup successfully")
            
        except Exception as e:
            logger.error(f"Error setting up LLM: {e}")
            raise
    
    async def generate_response(self, user_message: str, user_id: Optional[str] = None) -> str:
        """Generate intelligent response using RAG."""
        if not self.initialized or not self.llm:
            return self._fallback_response(user_message)
        
        try:
            # Analyze the type of query to provide contextual responses
            query_type = self._analyze_query_type(user_message)
            
            # Create a natural, contextual prompt for the assistant
            enhanced_query = f"""
            You are Aung Khant Phyo's personal assistant. A user has asked: "{user_message}"
            
            IMPORTANT RESPONSE GUIDELINES:
            
            Query Type: {query_type}
            
            1. GREETING QUERIES (hello, hi, hey, good morning):
               - Respond warmly: "Hi! I'm here to help you learn about Aung Khant Phyo. What would you like to know?"
               - Don't use "Hello!" at the start
               - Ask specifically what they want to know
            
            2. SPECIFIC TECHNICAL QUESTIONS (skills, experience, languages, projects):
               - NO greeting words (Hello, Hi) - get straight to the answer
               - Provide specific, detailed information
               - Be comprehensive but concise
               - Example: "Aung Khant Phyo is skilled in Python, TypeScript, Java..." (NOT "Hello! He's skilled in...")
            
            3. IDENTITY QUESTIONS (who is, tell me about, what does he do):
               - NO greeting words
               - Give a brief but informative overview
               - Include 2-3 key highlights about his background
               - Keep it under 100 words
            
            4. PROFESSIONAL INQUIRIES (hiring, contact, work):
               - Be professional and helpful
               - Provide relevant professional information
               - Don't start with greetings
            
            5. CONVERSATIONAL (thanks, help, random):
               - Respond naturally and appropriately
               - For thanks: just say "You're welcome!"
               - For help: ask what specifically they want to know
            
            CRITICAL RULES:
            - Only use greetings (Hello, Hi) if the user is greeting you
            - For non-greeting questions, jump straight into the answer
            - Be specific and informative, not generic
            - Keep responses conversational but focused
            - Don't mention technical terms like "documents", "knowledge base", etc.
            - If unsure, provide what you know and suggest contacting him directly
            """
            
            # Generate response using RAG
            response = self.llm.generate_content(enhanced_query)
            
            if response and hasattr(response, 'text') and response.text:
                # Clean up the response
                clean_response = response.text.strip()
                
                # Limit response length for Telegram
                if len(clean_response) > 4000:
                    clean_response = clean_response[:3900] + "...\n\nFor more details, feel free to contact Aung Khant Phyo directly!"
                
                return clean_response
            else:
                return self._fallback_response(user_message)
                
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            return self._fallback_response(user_message)
    
    def _analyze_query_type(self, message: str) -> str:
        """Analyze the type of query to provide appropriate response style."""
        msg_lower = message.lower().strip()
        
        # Greeting queries
        if any(greeting in msg_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            return "greeting"
        
        # Specific technical questions
        elif any(tech in msg_lower for tech in ['skills', 'programming', 'languages', 'technology', 'technical', 'experience', 'projects', 'work']):
            return "technical"
        
        # Identity questions
        elif any(identity in msg_lower for identity in ['who is', 'tell me about', 'what does', 'about him']):
            return "identity"
        
        # Professional inquiries
        elif any(prof in msg_lower for prof in ['hire', 'hiring', 'contact', 'reach', 'professional', 'work with']):
            return "professional"
        
        # Thanks
        elif any(thanks in msg_lower for thanks in ['thanks', 'thank you', 'thx']):
            return "thanks"
        
        # Help
        elif 'help' in msg_lower:
            return "help"
        
        # Default conversational
        else:
            return "conversational"
    
    def _fallback_response(self, text: str) -> str:
        """Fallback response when RAG is not available."""
        t = text.lower().strip()
        
        if any(greeting in t for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            return "Hello! I'm Aung Khant Phyo's assistant. How can I help you learn more about him today?"
        elif any(thanks in t for thanks in ['thanks', 'thank you', 'thx']):
            return "You're welcome! Feel free to ask me anything else about Aung Khant Phyo."
        elif any(question in t for question in ['what', 'how', 'why', 'when', 'where', 'who']):
            return "That's a great question about Aung Khant Phyo! I'd love to help, but I'm currently updating my information. You can reach out to him directly for the most current details."
        elif 'help' in t:
            return "I'm here to help you learn about Aung Khant Phyo! You can ask me about his background, experience, projects, or anything else you'd like to know."
        else:
            return "Thanks for reaching out! I'm Aung Khant Phyo's assistant. What would you like to know about him?"
    
    async def reload_data(self) -> bool:
        """Reload data from Google Drive (useful for updates)."""
        if not self.initialized or not self.rag_corpus or not VERTEXAI_AVAILABLE:
            return False
        
        try:
            if hasattr(self.rag_corpus, 'name') and self.rag_corpus.name:
                logger.info("Reloading data from Google Drive...")
                rag.import_files( # type: ignore
                    corpus_name=self.rag_corpus.name,
                    paths=[f"https://drive.google.com/drive/folders/{self.drive_folder_id}"],
                    chunk_size=512,
                    chunk_overlap=50,
                )
                logger.info("Data reloaded successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Error reloading data: {e}")
            return False
    
    async def cleanup(self):
        """Clean up RAG resources (use with caution)."""
        if not VERTEXAI_AVAILABLE:
            return
            
        try:
            from vertexai.preview import rag
            if self.rag_corpus and hasattr(self.rag_corpus, 'name') and self.rag_corpus.name:
                rag.delete_corpus(name=self.rag_corpus.name)
                logger.info("RAG corpus deleted")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Global RAG service instance
rag_service = RAGService()
