import os
import pickle
import logging
from typing import List, Dict
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from app.config import settings

logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        self.vector_store = None
        self.session_path = settings.STORAGE_DIR / session_id

    def create_vector_store(self, crawled_data: List[dict]) -> None:
        """Create FAISS vector store from crawled data"""
        logger.info(f"Creating vector store for session {self.session_id}")

        # Create session directory
        self.session_path.mkdir(exist_ok=True)

        # Convert crawled data to documents
        documents = []
        for page_data in crawled_data:
            doc = Document(
                page_content=page_data['content'],
                metadata={
                    'url': page_data['url'],
                    'title': page_data['title'],
                    'depth': page_data['depth']
                }
            )
            documents.append(doc)

        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
        )
        split_docs = text_splitter.split_documents(documents)
        logger.info(f"Split into {len(split_docs)} chunks")

        # Create FAISS vector store
        self.vector_store = FAISS.from_documents(split_docs, self.embeddings)

        # Save vector store
        self._save_vector_store()
        logger.info(f"Vector store created and saved for session {self.session_id}")

    def load_vector_store(self) -> bool:
        """Load existing vector store from disk"""
        try:
            vector_store_path = self.session_path / "faiss_index"
            if vector_store_path.exists():
                self.vector_store = FAISS.load_local(
                    str(vector_store_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info(f"Vector store loaded for session {self.session_id}")
                return True
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
        return False

    def _save_vector_store(self) -> None:
        """Save vector store to disk"""
        if self.vector_store:
            vector_store_path = self.session_path / "faiss_index"
            self.vector_store.save_local(str(vector_store_path))

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Perform similarity search on vector store"""
        if not self.vector_store:
            if not self.load_vector_store():
                raise ValueError(f"No vector store found for session {self.session_id}")

        results = self.vector_store.similarity_search(query, k=k)
        return results

    def delete_session(self) -> None:
        """Delete all session data including vector store"""
        try:
            if self.session_path.exists():
                import shutil
                shutil.rmtree(self.session_path)
                logger.info(f"Session {self.session_id} deleted")
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")