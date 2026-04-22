"""Chat service that wraps V1 ChatbotApp logic"""

import logging
import sys
from pathlib import Path
from typing import Generator, Optional

# Add parent directory to path to import V1 modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database import DatabaseRepository
from auth_service import AuthenticationService
from app import ChatbotApp
from app.session import ConversationSession

logger = logging.getLogger(__name__)


class ChatService:
    """
    Wraps V1 ChatbotApp logic for API usage.
    Handles initialization, session management, and streaming responses.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern - reuse same instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize ChatService with V1 components"""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing ChatService with V1 components...")
            
            # Initialize database and auth
            self.db = DatabaseRepository("data/chatbot.db")
            self.auth = AuthenticationService(self.db)
            
            # Initialize ChatbotApp (contains RAGEngine, MessageHandler, etc.)
            self.chatbot_app = ChatbotApp(self.db, self.auth)
            
            # Session storage (in-memory for now, could use Redis later)
            self.sessions: dict[str, ConversationSession] = {}
            
            self._initialized = True
            logger.info("✅ ChatService initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChatService: {e}", exc_info=True)
            raise
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> ConversationSession:
        """Get existing session or create new one"""
        if session_id and session_id in self.sessions:
            logger.info(f"Using existing session: {session_id}")
            return self.sessions[session_id]
        
        # Create new session
        session = ConversationSession()
        self.sessions[session.session_id] = session
        logger.info(f"Created new session: {session.session_id}")
        return session
    
    def stream_chat_response(
        self,
        message: str,
        session_id: Optional[str] = None,
        files: list = None,
    ) -> Generator[dict, None, None]:
        """
        Stream chat response using V1 MessageHandler.
        Yields partial response chunks as they arrive.
        """
        if not files:
            files = []
        
        # Get or create session
        session = self.get_or_create_session(session_id)
        
        # Hardcoded user_id for now (JWT will handle this in Phase 2)
        user_id = 1
        
        try:
            # Get message handler from ChatbotApp
            msg_handler = self.chatbot_app.msg_handler
            
            # Stream response from V1 logic
            response_chunks = []
            for chunk in msg_handler.process_stream(message, files, session, user_id):
                response_chunks.append(chunk)
                # Yield response chunk
                yield {
                    "type": "response",
                    "content": chunk,
                }
            
            # Yield metadata after streaming completes
            full_response = "".join(response_chunks)
            chunks_retrieved = 0  # TODO: Extract from RAG results
            
            yield {
                "type": "metadata",
                "data": {
                    "session_id": session.session_id,
                    "chunks_retrieved": chunks_retrieved,
                    "conversation_type": "TECHNICAL",  # TODO: Extract from msg_handler
                }
            }
            
        except Exception as e:
            logger.error(f"Error in stream_chat_response: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"Error: {str(e)}",
            }
    
    def clear_session(self, session_id: str) -> bool:
        """Clear session from memory"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session: {session_id}")
            return True
        return False
