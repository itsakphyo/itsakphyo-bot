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
            # Preprocess the message to handle pronouns and context
            processed_message = self._preprocess_message(user_message)
            
            # Analyze the type of query to provide contextual responses
            query_type = self._analyze_query_type(processed_message)
            
            # Create a natural, contextual prompt for the assistant
            enhanced_query = f"""
            You are Aung Khant Phyo's personal AI assistant. A user has asked: "{processed_message}"

            He, Him, His has good change to refer to Aung Khant Phyo. Sometime user might use slang or short word, analyze carefully.
            
            CRITICAL RESPONSE GUIDELINES - FOLLOW EXACTLY:
            
            Query Type: {query_type}
            
            1. GREETING QUERIES (hello, hi, hey, good morning):
               - Respond: "Hi! I'm here to help you learn about Aung Khant Phyo. What would you like to know?"
               - Always ask what they want to know specifically
            
            2. TECHNICAL/SPECIFIC QUESTIONS (skills, experience, languages, projects, background):
               - NEVER start with greetings (Hello, Hi, Hey)
               - Jump straight into the answer
               - Be specific and detailed
               - Example: "Aung Khant Phyo is skilled in Python, TypeScript..." (NOT "Hello! He's skilled in...")
            
            3. IDENTITY QUESTIONS (who is, tell me about, what does he do):
               - NEVER start with greetings
               - Give a comprehensive but concise overview
               - Include his role, background, and key skills
               - Keep it informative but under 150 words
            
            4. SHORT CONVERSATIONAL RESPONSES:
               - "Thanks/Thank you" → Just say "You're welcome!"
               - "Ok" → Say "Is there anything else you'd like to know about Aung Khant Phyo?"
               - "Very good/Great/Wow" → Say "Great! Feel free to ask me anything else about him."
               - "Yes" → Ask "What specifically would you like to know about Aung Khant Phyo?"
               - "No" → Say "No problem! Feel free to ask if you want to know more about Aung Khant Phyo later."
               - "Nothing" → Say "That's fine! I'm here if you want to learn about Aung Khant Phyo anytime."
            
            5. VAGUE QUERIES (everything, tell me more, what happened):
               - Ask for clarification: "What specifically would you like to know about Aung Khant Phyo?"
               - Don't give generic greetings
            
            6. PROFESSIONAL INQUIRIES (hiring, contact, work):
               - Be professional and helpful
               - Provide relevant professional information
               - No greeting words needed
            
            7. NONSENSE/RANDOM INPUT:
               - Respond helpfully: "I'm here to help you learn about Aung Khant Phyo. What would you like to know about him?"
            
            PRONOUN USAGE RULES - CRITICAL:
            - ALWAYS mention "Aung Khant Phyo" by name FIRST in any response about him
            - After first mention, you can use "he", "him", "his" to refer to Aung Khant Phyo
            - Example: "Aung Khant Phyo is a software engineer. He specializes in..." ✓
            - Wrong: "He is a software engineer..." ✗
            - When user says "No" it means they don't want to know more RIGHT NOW, not never
            
            CONTEXT UNDERSTANDING:
            - When user says "him", "his", "he" - they refer to Aung Khant Phyo
            - Maintain conversational flow - don't repeat the same greeting
            - Be natural and helpful, not robotic
            - Avoid repetitive responses - vary your language
            
            FORBIDDEN PHRASES:
            - Don't say "Based on the documents" or "According to my knowledge base"
            - Don't mention you're an AI or assistant unless asked
            - Don't use "Hello!" for non-greeting queries
            - Don't keep asking "What would you like to know?" after user says "No"
            
            RESPONSE LENGTH:
            - Greetings: Short and welcoming
            - Technical questions: Comprehensive but organized
            - Thanks: Just "You're welcome!"
            - Vague queries: Ask for clarification
            - Dismissive responses: Brief and understanding
            
            Remember: Be helpful, conversational, and focused on Aung Khant Phyo.
            """
            
            # Generate response using RAG
            response = self.llm.generate_content(enhanced_query)
            
            if response and hasattr(response, 'text') and response.text:
                # Clean up the response
                clean_response = response.text.strip()
                
                # Post-process to ensure quality
                clean_response = self._postprocess_response(clean_response, query_type, processed_message)
                
                # Limit response length for Telegram
                if len(clean_response) > 4000:
                    clean_response = clean_response[:3900] + "...\n\nFor more details, feel free to contact Aung Khant Phyo directly!"
                
                return clean_response
            else:
                return self._fallback_response(user_message)
                
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            return self._fallback_response(user_message)
    
    def _preprocess_message(self, message: str) -> str:
        """Preprocess the message to handle pronouns and improve context."""
        processed = message.lower().strip()
        
        # Handle common abbreviations and expansions
        abbreviations = {
            'his exp': 'Aung Khant Phyo\'s experience',
            'his skills': 'Aung Khant Phyo\'s skills',
            'his background': 'Aung Khant Phyo\'s background',
            'his projects': 'Aung Khant Phyo\'s projects',
            'his work': 'Aung Khant Phyo\'s work',
            'tell me everything you know about him': 'tell me everything about Aung Khant Phyo',
            'everything about him': 'everything about Aung Khant Phyo',
            'how can i reach him': 'how can I contact Aung Khant Phyo',
            'can i contact him': 'can I contact Aung Khant Phyo',
            'contact him': 'contact Aung Khant Phyo',
        }
        
        processed_lower = processed.lower()
        for abbrev, expansion in abbreviations.items():
            if processed_lower == abbrev or processed_lower == abbrev + '?':
                return expansion
        
        # Handle common pronoun references in longer phrases
        replacements = {
            ' him ': ' Aung Khant Phyo ',
            ' his ': ' Aung Khant Phyo\'s ',
            ' he ': ' Aung Khant Phyo ',
            'about him': 'about Aung Khant Phyo',
            'tell me about him': 'tell me about Aung Khant Phyo',
            'who is he': 'who is Aung Khant Phyo',
            'what does he': 'what does Aung Khant Phyo',
            'where is he': 'where is Aung Khant Phyo',
            'what about him': 'what about Aung Khant Phyo',
            'tell me more about him': 'tell me more about Aung Khant Phyo',
        }
        
        for old, new in replacements.items():
            if old in processed_lower:
                # Find the position and replace with proper case
                pos = processed_lower.find(old)
                if pos != -1:
                    processed = processed[:pos] + new + processed[pos + len(old):]
                    processed_lower = processed.lower()
        
        return processed
    
    def _postprocess_response(self, response: str, query_type: str, original_query: str) -> str:
        """Post-process the response to ensure quality and appropriateness."""
        # Remove any unwanted prefixes
        unwanted_prefixes = [
            "Based on the documents",
            "According to my knowledge",
            "From the information provided",
            "The documents show that",
        ]
        
        for prefix in unwanted_prefixes:
            if response.startswith(prefix):
                # Find the next sentence start
                next_sentence = response.find('. ') + 2
                if next_sentence > 1:
                    response = response[next_sentence:]
        
        # Ensure appropriate response for query type
        original_lower = original_query.lower().strip()
        
        # Handle thanks responses
        if original_lower in ['thanks', 'thank you', 'thx']:
            return "You're welcome!"
        
        # Handle short acknowledgments
        if original_lower in ['ok', 'okay']:
            return "Is there anything else you'd like to know about Aung Khant Phyo?"
        
        if original_lower in ['very good', 'great', 'wow that many', 'wow']:
            return "Great! Feel free to ask me anything else about him."
        
        if original_lower == 'yes':
            return "What specifically would you like to know about Aung Khant Phyo?"
        
        # Handle dismissive responses
        if original_lower in ['no', 'nope']:
            return "No problem! Feel free to ask if you want to know more about Aung Khant Phyo later."
        
        if original_lower in ['nothing', 'nah']:
            return "That's fine! I'm here if you want to learn about Aung Khant Phyo anytime."
        
        # Handle humor/casual comments
        if 'funny' in original_lower or 'haha' in original_lower:
            return "Glad you enjoyed that! What else would you like to know about Aung Khant Phyo?"
        
        # Handle vague queries
        if original_lower in ['everything', 'tell me everything', 'what happened']:
            return "What specifically would you like to know about Aung Khant Phyo? I can tell you about his background, skills, experience, projects, or anything else you're curious about!"
        
        return response.strip()
    
    def _analyze_query_type(self, message: str) -> str:
        """Analyze the type of query to provide appropriate response style."""
        msg_lower = message.lower().strip()
        
        # Handle empty or very short messages
        if not msg_lower or len(msg_lower) < 2:
            return "help"
        
        # Greeting queries
        if any(greeting in msg_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            return "greeting"
        
        # Thanks responses
        if any(thanks in msg_lower for thanks in ['thanks', 'thank you', 'thx']):
            return "thanks"
        
        # Short conversational responses
        if msg_lower in ['ok', 'okay', 'yes', 'very good', 'great', 'wow', 'wow that many', 'nice', 'no', 'nope', 'nothing', 'nah']:
            return "conversational"
        
        # Humor/casual comments
        if any(casual in msg_lower for casual in ['funny', 'haha', 'lol', 'cool']):
            return "conversational"
        
        # Vague queries that need clarification
        if msg_lower in ['everything', 'tell me everything', 'what happened', 'what about']:
            return "vague"
        
        # Specific technical questions
        elif any(tech in msg_lower for tech in ['skills', 'programming', 'languages', 'technology', 'technical', 'experience', 'projects', 'work', 'exp']):
            return "technical"
        
        # Identity questions
        elif any(identity in msg_lower for identity in ['who is', 'tell me about', 'what does', 'about him', 'about aung']):
            return "identity"
        
        # Professional inquiries
        elif any(prof in msg_lower for prof in ['hire', 'hiring', 'contact', 'reach', 'professional', 'work with', 'email', 'phone']):
            return "professional"
        
        # Help requests
        elif 'help' in msg_lower:
            return "help"
        
        # Random/nonsense input
        elif not any(char.isalpha() for char in msg_lower) or len(set(msg_lower.replace(' ', ''))) <= 3:
            return "nonsense"
        
        # Default conversational
        else:
            return "conversational"
    
    def _fallback_response(self, text: str) -> str:
        """Fallback response when RAG is not available."""
        t = text.lower().strip()
        
        # Handle greetings
        if any(greeting in t for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            return "Hi! I'm here to help you learn about Aung Khant Phyo. What would you like to know?"
        
        # Handle thanks
        elif any(thanks in t for thanks in ['thanks', 'thank you', 'thx']):
            return "You're welcome!"
        
        # Handle short conversational responses
        elif t in ['ok', 'okay']:
            return "Is there anything else you'd like to know about Aung Khant Phyo?"
        elif t in ['yes']:
            return "What specifically would you like to know about Aung Khant Phyo?"
        elif t in ['very good', 'great', 'wow', 'nice']:
            return "Great! Feel free to ask me anything else about him."
        elif t in ['no', 'nope']:
            return "No problem! Feel free to ask if you want to know more about Aung Khant Phyo later."
        elif t in ['nothing', 'nah']:
            return "That's fine! I'm here if you want to learn about Aung Khant Phyo anytime."
        
        # Handle vague queries
        elif t in ['everything', 'tell me everything', 'what happened']:
            return "What specifically would you like to know about Aung Khant Phyo? I can tell you about his background, skills, experience, projects, or anything else you're curious about!"
        
        # Handle questions about skills/experience
        elif any(word in t for word in ['skills', 'experience', 'programming', 'work']):
            return "Aung Khant Phyo is a skilled Software Engineer and AI Developer. He specializes in Python, TypeScript, machine learning, and backend development. I'd love to provide more details, but I'm currently updating my information. You can reach out to him directly for the most current details."
        
        # Handle identity questions
        elif any(question in t for question in ['who is', 'tell me about', 'what does']):
            return "Aung Khant Phyo is a Software Engineer and AI Developer based in Bangkok, Thailand. He's experienced in backend engineering, machine learning, and data analysis. I'd love to provide more details, but I'm currently updating my information. You can reach out to him directly for the most current details."
        
        # Handle help requests
        elif 'help' in t:
            return "I'm here to help you learn about Aung Khant Phyo! You can ask me about his background, experience, projects, skills, or anything else you'd like to know."
        
        # Handle nonsense or random input
        elif not any(char.isalpha() for char in t) or len(set(t.replace(' ', ''))) <= 3:
            return "I'm here to help you learn about Aung Khant Phyo. What would you like to know about him?"
        
        # Handle other questions
        elif any(question in t for question in ['what', 'how', 'why', 'when', 'where']):
            return "That's a great question about Aung Khant Phyo! I'd love to help, but I'm currently updating my information. You can reach out to him directly for the most current details."
        
        # Default response
        else:
            return "I'm here to help you learn about Aung Khant Phyo. What would you like to know about him?"
    
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
