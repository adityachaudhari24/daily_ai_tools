from pydantic import BaseModel, HttpUrl
from typing import Optional, List

class CrawlRequest(BaseModel):
    url: HttpUrl
    max_depth: Optional[int] = 3
    max_pages: Optional[int] = 100

class CrawlResponse(BaseModel):
    session_id: str
    url: str
    pages_crawled: int
    urls_scraped: List[str]
    status: str
    message: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    message: str
    response: str
    sources: Optional[List[str]] = []