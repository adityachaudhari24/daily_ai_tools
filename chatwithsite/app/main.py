import logging
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import CrawlRequest, CrawlResponse, ChatRequest, ChatResponse
from app.crawler import WebsiteCrawler
from app.vector_store import VectorStoreManager
from app.chat_service import chat_manager
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Chat with Website API",
    description="Crawl websites and chat with their content using AI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Chat with Website API",
        "endpoints": {
            "POST /crawl": "Crawl a website and create a chat session",
            "POST /chat": "Chat with crawled website content",
            "DELETE /session/{session_id}": "Delete a chat session",
            "GET /health": "Health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/crawl", response_model=CrawlResponse)
async def crawl_website(request: CrawlRequest):
    """
    Crawl a website and prepare it for chat interactions

    - **url**: The base URL to crawl
    - **max_depth**: Maximum depth to crawl (default: 3)
    - **max_pages**: Maximum number of pages to crawl (default: 100)
    """
    try:
        # Validate OpenAI API key
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY in .env file"
            )

        # Generate unique session ID
        session_id = str(uuid.uuid4())
        logger.info(f"Starting crawl for {request.url} with session {session_id}")

        # Initialize crawler
        crawler = WebsiteCrawler(
            base_url=str(request.url),
            max_depth=request.max_depth,
            max_pages=request.max_pages
        )

        # Crawl the website
        crawled_data = await crawler.crawl_website()

        if not crawled_data or not crawled_data.get('data'):
            raise HTTPException(
                status_code=400,
                detail="Failed to crawl website. No pages were successfully crawled."
            )

        # Create vector store
        vector_manager = VectorStoreManager(session_id)
        vector_manager.create_vector_store(crawled_data['data'])

        logger.info(f"Crawl completed for session {session_id}")

        return CrawlResponse(
            session_id=session_id,
            url=str(request.url),
            pages_crawled=crawled_data['indexed_count'],
            urls_scraped=crawled_data['urls_visited'],
            status="success",
            message=f"Successfully crawled {crawled_data['indexed_count']} pages from {crawled_data['visited_count']} unique URLs. Use session_id to start chatting."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during crawl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error crawling website: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat_with_website(request: ChatRequest):
    """
    Chat with the crawled website content

    - **session_id**: The session ID from the crawl response
    - **message**: Your question or message
    """
    try:
        # Validate OpenAI API key
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured"
            )

        # Get or create chat session
        chat_session = chat_manager.get_or_create_session(request.session_id)

        # Process the chat message
        result = chat_session.chat(request.message)

        return ChatResponse(
            session_id=request.session_id,
            message=request.message,
            response=result["response"],
            sources=result["sources"]
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a chat session and all associated data

    - **session_id**: The session ID to delete
    """
    try:
        chat_manager.delete_session(session_id)
        return {
            "status": "success",
            "message": f"Session {session_id} deleted successfully"
        }
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)