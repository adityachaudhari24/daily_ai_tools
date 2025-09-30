import asyncio
from typing import List, Set, Dict
from urllib.parse import urljoin, urlparse
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
import logging

logger = logging.getLogger(__name__)

class WebsiteCrawler:
    def __init__(self, base_url: str, max_depth: int = 3, max_pages: int = 100):
        """
        Initialize the website crawler.

        Args:
            base_url: The starting URL to crawl
            max_depth: Maximum depth of internal links to follow
            max_pages: Maximum number of pages to crawl
        """
        self.base_url = base_url
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.visited_urls: Set[str] = set()
        self.crawled_data: List[dict] = []
        self.base_domain = urlparse(base_url).netloc
        self.indexed_count = 0

    def _is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to the same domain as base URL"""
        try:
            return urlparse(url).netloc == self.base_domain
        except Exception:
            return False

    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and trailing slashes"""
        try:
            parsed = urlparse(url)
            # Remove fragment
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            # Remove trailing slash for consistency (except for root)
            if normalized.endswith('/') and len(parsed.path) > 1:
                normalized = normalized[:-1]
            return normalized
        except Exception:
            return url

    def _extract_links_from_result(self, result) -> List[str]:
        """Extract all links from crawl result"""
        links = []

        if not result.links:
            return links

        try:
            # Handle different link formats from crawl4ai
            if isinstance(result.links, dict):
                # Try to get internal links first
                if 'internal' in result.links:
                    links_list = result.links['internal']
                    if isinstance(links_list, list):
                        for link in links_list:
                            # Each link can be a dict with 'href' or a string
                            if isinstance(link, dict) and 'href' in link:
                                links.append(link['href'])
                            elif isinstance(link, str):
                                links.append(link)

                # Get all other link categories
                for key, value in result.links.items():
                    if isinstance(value, list) and key != 'internal':
                        for link in value:
                            if isinstance(link, dict) and 'href' in link:
                                links.append(link['href'])
                            elif isinstance(link, str):
                                links.append(link)

            # Handle list format
            elif isinstance(result.links, list):
                for link in result.links:
                    if isinstance(link, dict) and 'href' in link:
                        links.append(link['href'])
                    elif isinstance(link, str):
                        links.append(link)

        except Exception as e:
            logger.error(f"Error extracting links: {str(e)}")

        return links

    async def crawl_page(self, crawler: AsyncWebCrawler, url: str, depth: int = 0) -> List[str]:
        """
        Crawl a single page and return discovered internal links.

        Args:
            crawler: AsyncWebCrawler instance
            url: URL to crawl
            depth: Current depth in the crawl tree

        Returns:
            List of discovered internal links
        """
        if depth > self.max_depth or len(self.visited_urls) >= self.max_pages:
            return []

        normalized_url = self._normalize_url(url)
        if normalized_url in self.visited_urls:
            return []

        self.visited_urls.add(normalized_url)
        logger.info(f"Crawling: {normalized_url} (depth: {depth}, indexed: {self.indexed_count})")

        try:
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                check_robots_txt=True,
                stream=False
            )

            result = await crawler.arun(url=url, config=run_config)

            if result.success and result.markdown:
                # Store crawled data
                self.crawled_data.append({
                    'url': result.url,
                    'content': result.markdown,
                    'title': result.metadata.get('title', '') if result.metadata else '',
                    'depth': depth
                })
                self.indexed_count += 1
                logger.info(f"✓ Indexed: {normalized_url}")

                # Extract all links from the page
                raw_links = self._extract_links_from_result(result)
                logger.debug(f"Found {len(raw_links)} raw links on page")

                # Filter for internal links only
                internal_links = []
                for link in raw_links:
                    try:
                        # Convert relative URLs to absolute
                        absolute_url = urljoin(url, link)

                        # Only keep same-domain links
                        if self._is_same_domain(absolute_url):
                            normalized_link = self._normalize_url(absolute_url)

                            # Skip if already visited
                            if normalized_link not in self.visited_urls:
                                internal_links.append(absolute_url)
                                logger.debug(f"Discovered internal link: {normalized_link}")

                    except Exception as e:
                        logger.debug(f"Error processing link {link}: {str(e)}")

                logger.info(f"Found {len(internal_links)} new internal links at depth {depth}")
                return internal_links

        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")

        return []

    async def crawl_website(self) -> Dict[str, any]:
        """
        Crawl entire website starting from base URL, following internal links and deep links.

        Returns:
            Dictionary containing:
                - data: List of crawled page data
                - indexed_count: Number of pages successfully indexed
                - visited_count: Total number of unique URLs visited
        """
        logger.info(f"Starting crawl of {self.base_url} (max_depth={self.max_depth}, max_pages={self.max_pages})")

        browser_config = BrowserConfig(headless=True, verbose=False)

        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Initialize queue with base URL at depth 0
            urls_to_crawl = [(self.base_url, 0)]

            while urls_to_crawl and len(self.visited_urls) < self.max_pages:
                current_url, current_depth = urls_to_crawl.pop(0)

                # Skip if we've exceeded max depth
                if current_depth > self.max_depth:
                    continue

                # Crawl the current page and get discovered links
                discovered_links = await self.crawl_page(crawler, current_url, current_depth)

                # Add discovered internal links to queue with incremented depth
                for link in discovered_links:
                    if len(self.visited_urls) < self.max_pages:
                        urls_to_crawl.append((link, current_depth + 1))

                # Be respectful to the server
                await asyncio.sleep(0.5)

        logger.info(f"✓ Crawling completed!")
        logger.info(f"  - Pages indexed: {self.indexed_count}")
        logger.info(f"  - Unique URLs visited: {len(self.visited_urls)}")
        logger.info(f"  - Max depth reached: {max([data['depth'] for data in self.crawled_data]) if self.crawled_data else 0}")

        return {
            'data': self.crawled_data,
            'indexed_count': self.indexed_count,
            'visited_count': len(self.visited_urls),
            'urls_visited': list(self.visited_urls)
        }


async def index_website(url: str, max_depth: int = 3, max_pages: int = 100) -> Dict[str, any]:
    """
    Convenience function to index a website with internal links and deep links.

    Args:
        url: The website URL to index
        max_depth: Maximum depth of internal links to follow (default: 3)
        max_pages: Maximum number of pages to index (default: 100)

    Returns:
        Dictionary containing indexed data and statistics:
            - data: List of crawled pages
            - indexed_count: Number of pages indexed
            - visited_count: Number of unique URLs visited
            - urls_visited: List of all visited URLs
    """
    crawler = WebsiteCrawler(url, max_depth=max_depth, max_pages=max_pages)
    return await crawler.crawl_website()
