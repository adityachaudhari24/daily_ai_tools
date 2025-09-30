# Chat with Website

A powerful Python-based tool that crawls entire websites (including sublinks) and enables you to chat with the content using AI. Built with FastAPI, Crawl4AI, FAISS, and OpenAI.

## Features

- 🕷️ **Smart Web Crawler**: Crawls websites with configurable depth and page limits
- 🔗 **Sublink Discovery**: Automatically discovers and crawls internal links
- 💬 **AI-Powered Chat**: Chat with website content using OpenAI's GPT models
- 🧠 **Context Preservation**: Maintains conversation context within sessions
- 📚 **Vector Search**: Uses FAISS for efficient semantic search
- 🔄 **Session Management**: Multiple independent chat sessions
- 🚀 **REST API**: Easy integration with FastAPI endpoints

## Project Structure

```
chatwithsite/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application and endpoints
│   ├── config.py            # Configuration and settings
│   ├── models.py            # Pydantic models
│   ├── crawler.py           # Website crawling logic
│   ├── vector_store.py      # FAISS vector store management
│   └── chat_service.py      # Chat session management
├── storage/                 # Session data and vector stores (auto-created)
├── data/                    # Temporary data storage (auto-created)
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Installation

### Prerequisites

- Python 3.10 or higher
- OpenAI API key

### Setup Steps

1. **Clone and navigate to the project**
   ```bash
   cd chatwithsite
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  
   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```

5. **Install Playwright (required by Crawl4AI)**
   ```bash
   playwright install
   ```

## Usage

### Starting the Server

**Standard way (recommended):**
```bash
# Run from the chatwithsite directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Alternative way:**
```bash
cd app
python main.py
```

The API will be available at: `http://localhost:8000`

Interactive API documentation: `http://localhost:8000/docs`

### API Endpoints

#### 1. **Crawl a Website**

**POST** `/crawl`

Crawls a website and creates a chat session.

**Request Body:**
```json
{
  "url": "https://example.com",
  "max_depth": 3,
  "max_pages": 100
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://example.com",
  "pages_crawled": 45,
  "status": "success",
  "message": "Successfully crawled 45 pages. Use session_id to start chatting."
}
```

**Postman Example:**
- Method: POST
- URL: `http://localhost:8000/crawl`
- Headers: `Content-Type: application/json`
- Body: Raw JSON (see above)

#### 2. **Chat with Website**

**POST** `/chat`

Ask questions about the crawled website content.

**Request Body:**
```json
{
  "session_id": "16c30e96-0caf-4aa0-aa4f-afe028de7f53",
  "message": "What is this website about?"
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "What is this website about?",
  "response": "Based on the content, this website is about...",
  "sources": [
    "https://example.com/about",
    "https://example.com/home"
  ]
}
```

**Postman Example:**
- Method: POST
- URL: `http://localhost:8000/chat`
- Headers: `Content-Type: application/json`
- Body: Raw JSON (see above)

#### 3. **Delete Session**

**DELETE** `/session/{session_id}`

Removes session data and cleans up vector store.

**Response:**
```json
{
  "status": "success",
  "message": "Session 550e8400-e29b-41d4-a716-446655440000 deleted successfully"
}
```

**Postman Example:**
- Method: DELETE
- URL: `http://localhost:8000/session/550e8400-e29b-41d4-a716-446655440000`

#### 4. **Health Check**

**GET** `/health`

Check if the service is running.

**Response:**
```json
{
  "status": "healthy"
}
```

## Configuration

Edit `app/config.py` to customize:

```python
# Crawler settings
MAX_CRAWL_DEPTH: int = 3        # Maximum depth to crawl
MAX_PAGES_PER_SITE: int = 100   # Maximum pages to crawl

# LLM settings
MODEL_NAME: str = "gpt-3.5-turbo"  # OpenAI model
TEMPERATURE: float = 0.7            # Response creativity
MAX_TOKENS: int = 500               # Response length

# Vector store settings
CHUNK_SIZE: int = 1000              # Text chunk size
CHUNK_OVERLAP: int = 200            # Chunk overlap
```

## Example Workflow

### Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Crawl a website
response = requests.post(f"{BASE_URL}/crawl", json={
    "url": "https://example.com",
    "max_depth": 2,
    "max_pages": 50
})
session_id = response.json()["session_id"]
print(f"Session ID: {session_id}")

# 2. Chat with the website
response = requests.post(f"{BASE_URL}/chat", json={
    "session_id": session_id,
    "message": "What are the main topics covered?"
})
print(f"Response: {response.json()['response']}")

# 3. Continue the conversation (context preserved)
response = requests.post(f"{BASE_URL}/chat", json={
    "session_id": session_id,
    "message": "Can you tell me more about the first topic?"
})
print(f"Response: {response.json()['response']}")

# 4. Clean up when done
requests.delete(f"{BASE_URL}/session/{session_id}")
```

### Using cURL

```bash
# Crawl website
curl -X POST "http://localhost:8000/crawl" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "max_depth": 2, "max_pages": 50}'

# Chat (replace SESSION_ID with actual session ID)
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "SESSION_ID", "message": "What is this about?"}'

# Delete session
curl -X DELETE "http://localhost:8000/session/SESSION_ID"
```

## How It Works

1. **Crawling Phase**:
   - Starts from the provided URL
   - Discovers internal links within the same domain
   - Crawls up to specified depth and page limit
   - Extracts content in markdown format

2. **Indexing Phase**:
   - Splits content into chunks (1000 chars with 200 overlap)
   - Creates embeddings using OpenAI
   - Stores in FAISS vector database
   - Saves to session-specific storage

3. **Chat Phase**:
   - Converts questions to embeddings
   - Performs similarity search in FAISS
   - Retrieves relevant chunks
   - Sends to OpenAI with context
   - Maintains conversation history

4. **Cleanup Phase**:
   - Deletes session folder
   - Removes vector store files
   - Clears conversation memory

## Limitations & Notes

- **Session Cleanup**: Vector stores are currently wiped after each session (as per requirements). For persistent storage, modify `delete_session` behavior.
- **Rate Limiting**: Be respectful of target websites. The crawler includes 0.5s delays between requests.
- **Robots.txt**: Crawler respects robots.txt by default.
- **Same Domain Only**: Crawler only follows internal links within the same domain.
- **OpenAI Costs**: Each chat request consumes OpenAI API credits.

## Troubleshooting

### Common Issues

1. **"OpenAI API key not configured"**
   - Ensure `.env` file exists with valid `OPENAI_API_KEY`

2. **Playwright errors**
   - Run: `playwright install`

3. **"No vector store found for session"**
   - Session may have been deleted or expired
   - Re-crawl the website to create a new session

4. **Import errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Activate virtual environment

## Dependencies

- **FastAPI**: Web framework
- **Crawl4AI**: Web crawling
- **LangChain**: LLM orchestration
- **OpenAI**: Language model
- **FAISS**: Vector search
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server

## License

MIT License

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## Future Enhancements

- [ ] Persistent session storage
- [ ] Multiple LLM provider support
- [ ] Advanced crawling filters
- [ ] Export conversation history
- [ ] Batch crawling from sitemap
- [ ] Rate limiting and authentication
- [ ] WebSocket support for streaming responses