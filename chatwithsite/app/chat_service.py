import logging
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from app.config import settings
from app.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)

class ChatSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.vector_manager = VectorStoreManager(session_id)
        self.llm = ChatOpenAI(
            temperature=settings.TEMPERATURE,
            model_name=settings.MODEL_NAME,
            openai_api_key=settings.OPENAI_API_KEY,
            max_tokens=settings.MAX_TOKENS
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        self.qa_chain = None

    def initialize_chain(self) -> None:
        """Initialize the conversational retrieval chain"""
        if not self.vector_manager.load_vector_store():
            raise ValueError(f"No vector store found for session {self.session_id}")

        retriever = self.vector_manager.vector_store.as_retriever(
            search_kwargs={"k": 4}
        )

        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=self.memory,
            return_source_documents=True,
            verbose=True
        )
        logger.info(f"Chat chain initialized for session {self.session_id}")

    def chat(self, message: str) -> Dict[str, any]:
        """Process a chat message and return response with sources"""
        if not self.qa_chain:
            self.initialize_chain()

        try:
            result = self.qa_chain({"question": message})

            # Extract source URLs
            sources = []
            if "source_documents" in result:
                sources = list(set([
                    doc.metadata.get('url', 'Unknown')
                    for doc in result["source_documents"]
                ]))

            return {
                "response": result["answer"],
                "sources": sources
            }

        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            raise

class ChatManager:
    """Manages multiple chat sessions"""
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}

    def get_or_create_session(self, session_id: str) -> ChatSession:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ChatSession(session_id)
        return self.sessions[session_id]

    def delete_session(self, session_id: str) -> None:
        """Delete a chat session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.vector_manager.delete_session()
            del self.sessions[session_id]
            logger.info(f"Chat session {session_id} deleted")

# Global chat manager instance
chat_manager = ChatManager()