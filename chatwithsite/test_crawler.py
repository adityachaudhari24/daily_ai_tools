import asyncio
import logging
import sys
sys.path.insert(0, '/Users/aditya.chaudhari/Documents/projects/daily_ai_tools/chatwithsite')

from app.crawler import WebsiteCrawler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_crawl():
    url = "https://fastapi.tiangolo.com/"

    print(f"\n{'='*60}")
    print(f"Testing crawler with URL: {url}")
    print(f"Max depth: 2, Max pages: 10")
    print(f"{'='*60}\n")

    crawler = WebsiteCrawler(
        base_url=url,
        max_depth=2,
        max_pages=10
    )

    result = await crawler.crawl_website()

    print(f"\n{'='*60}")
    print(f"CRAWL RESULTS:")
    print(f"{'='*60}")
    print(f"Pages indexed: {result['indexed_count']}")
    print(f"Unique URLs visited: {result['visited_count']}")
    print(f"\nURLs crawled:")
    for i, url in enumerate(result['urls_visited'], 1):
        print(f"  {i}. {url}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(test_crawl())
