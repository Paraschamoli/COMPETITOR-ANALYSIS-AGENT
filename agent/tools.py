#!/usr/bin/env python3
"""
Tools and helpers for the Competitor Analysis Agent
"""

import asyncio
import subprocess
import json
import os
import tempfile
import shutil
import time
import logging
from agno.tools.tavily import TavilyTools
from agno.tools.serper import SerperTools
from agno.tools.firecrawl import FirecrawlTools
from .config import CRAWL4AI_AVAILABLE, YOUTUBE_AVAILABLE, YOUTUBE_API_KEY, GOOGLE_MAPS_SCRAPER_AVAILABLE, AGENT_REACH_AVAILABLE, check_agent_reach

logger = logging.getLogger(__name__)

# Re-export search tool classes so callers can `from agent.tools import TavilyTools, SerperTools`.
__all__ = [
    "TavilyTools",
    "SerperTools",
    "FirecrawlTools",
    "search_tools",
    "crawl_tools",
    "all_tools",
    "crawl4ai_scrape",
    "get_youtube_channel_stats",
    "scrape_google_maps",
    "google_maps_scraper_tool",
    "get_social_media_tools",
    "AgentReachTool",
]


def search_tools():
    """Serper only - Tavily quota exhausted, using Serper as primary"""
    tools = [TavilyTools(),SerperTools()]   # Tavily free tier exhausted, use Serper only
    return tools


class AgentReachTool:
    """
    Agent Reach tool for direct platform access.
    Wraps the agent-reach CLI commands for Twitter, Reddit, YouTube, Instagram, Facebook.
    """
    def __init__(self, max_retries: int = 3, retry_delay: int = 2):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _run_command(self, cmd: list, timeout: int = 30) -> str:
        """Run a command with retry logic."""
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    encoding='utf-8',
                    errors='replace'
                )
                if result.returncode == 0:
                    return result.stdout
                last_error = result.stderr
                logger.warning(f"Agent Reach attempt {attempt}/{self.max_retries} failed: {last_error}")
            except subprocess.TimeoutExpired:
                last_error = "Command timed out"
                logger.warning(f"Agent Reach attempt {attempt}/{self.max_retries} timed out")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Agent Reach attempt {attempt}/{self.max_retries} error: {e}")

            if attempt < self.max_retries:
                time.sleep(self.retry_delay * attempt)

        return f"Agent Reach failed after {self.max_retries} attempts: {last_error}"

    def search_twitter(self, query: str, count: int = 10) -> str:
        """Search Twitter using agent-reach twitter command."""
        if not check_agent_reach():
            return "Agent Reach not available - command not found"
        return self._run_command(['twitter', 'search', query, '-n', str(count)])

    def search_reddit(self, query: str) -> str:
        """Search Reddit using agent-reach rdt command."""
        if not check_agent_reach():
            return "Agent Reach not available - command not found"
        return self._run_command(['rdt', 'search', query])

    def search_youtube(self, query: str, count: int = 10) -> str:
        """Search YouTube using yt-dlp."""
        if not check_agent_reach():
            return "Agent Reach not available - command not found"
        return self._run_command(['yt-dlp', '--dump-json', f'ytsearch{count}:{query}'])

    def search_instagram(self, query: str) -> str:
        """Search Instagram - uses Twitter as proxy since direct IG not available."""
        if not check_agent_reach():
            return "Agent Reach not available - command not found"
        # Instagram search via Twitter as alternative
        return self._run_command(['twitter', 'search', f'{query} instagram', '-n', '5'])

    def search_facebook(self, query: str) -> str:
        """Search Facebook - uses Twitter as proxy since direct FB not available."""
        if not check_agent_reach():
            return "Agent Reach not available - command not found"
        return self._run_command(['twitter', 'search', f'{query} facebook page', '-n', '5'])

    def get_platform_stats(self, platform: str, handle: str) -> str:
        """Get stats for a specific platform handle."""
        if platform.lower() == 'twitter':
            return self._run_command(['twitter', 'user', handle])
        elif platform.lower() == 'youtube':
            return self._run_command(['yt-dlp', '--dump-json', f'ytchannel:{handle}'])
        return f"Platform {platform} stats not supported"


def get_social_media_tools():
    """
    Get tools optimized for social media analysis.
    Includes Agent Reach (if available) + search fallback with retry.
    """
    tools = []

    # Add Agent Reach if available
    if AGENT_REACH_AVAILABLE:
        # Note: We don't add it as a traditional tool but the agent can use it via function calls
        # The agent instructions reference agent_reach_search which is in config.py
        pass
    else:
        logger.info("Agent Reach not available, using search fallback")

    # Always add search tools as primary fallback
    tools.extend(search_tools())

    return tools


class RetryableSearchTool:
    """
    Wrapper for search tools that adds retry logic with exponential backoff.
    """
    def __init__(self, max_retries: int = 3, base_delay: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def search_with_retry(self, query: str, tool_name: str = "search") -> str:
        """
        Execute a search with retry logic.
        Returns results or error message after all retries exhausted.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                # Import tools fresh to avoid stale connections
                from agno.agent import Agent
                from agent.models import agent_model

                # Try each search tool in order
                for tool_class in [SerperTools, TavilyTools]:
                    try:
                        agent = Agent(
                            tools=[tool_class()],
                            model=agent_model(max_tokens=2000),
                            instructions=[f"Search for: {query}. Return results with business names, follower counts, and engagement data."],
                        )
                        result = agent.run(f"Search for: {query}")
                        content = getattr(result, 'content', '') or str(result)
                        if content and len(content.strip()) > 50:
                            return content
                    except Exception as e:
                        logger.warning(f"Search tool {tool_class.__name__} failed: {e}")
                        continue

                # If we got here, tools worked but returned empty
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying search in {delay}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)

            except Exception as e:
                logger.warning(f"Search attempt {attempt} failed with exception: {e}")
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** (attempt - 1))
                    time.sleep(delay)

        return f"Search failed for '{query}' after {self.max_retries} attempts. Try using different keywords or check API availability."


def crawl_tools():
    """Firecrawl tools for web scraping"""
    return [FirecrawlTools()]


def all_tools():
    """All available tools combined"""
    return search_tools() + crawl_tools()


async def crawl4ai_scrape(url: str) -> str:
    """Use Crawl4AI to scrape a URL — handles JS, anti-bot better than basic requests."""
    if not CRAWL4AI_AVAILABLE:
        return ""
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
        browser_config = BrowserConfig(headless=True, verbose=False)
        run_config = CrawlerRunConfig(cache_mode=CacheMode.ENABLED)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)
            return result.markdown[:5000] if result.markdown else ""
    except Exception as e:
        return f"Crawl4AI error: {e}"


def get_youtube_channel_stats(company_name: str) -> dict:
    """
    Fetch real YouTube stats using the free YouTube Data API.
    Returns subscriber count, video count, view count, recent videos.
    """
    if not YOUTUBE_AVAILABLE:
        return {"error": "YouTube API not configured. Add YOUTUBE_API_KEY to .env"}
    
    try:
        from googleapiclient.discovery import build as youtube_build
        yt = youtube_build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        
        # Search for the company channel
        search_resp = yt.search().list(
            q=f"{company_name} official",
            type="channel",
            part="snippet",
            maxResults=3
        ).execute()
        
        if not search_resp.get("items"):
            return {"error": f"No YouTube channel found for {company_name}"}
        
        channel_id = search_resp["items"][0]["id"]["channelId"]
        channel_title = search_resp["items"][0]["snippet"]["title"]
        
        # Get channel statistics
        stats_resp = yt.channels().list(
            id=channel_id,
            part="statistics,snippet"
        ).execute()
        
        stats = stats_resp["items"][0]["statistics"]
        
        # Get recent videos (last 5)
        videos_resp = yt.search().list(
            channelId=channel_id,
            type="video",
            part="snippet",
            order="date",
            maxResults=5
        ).execute()
        
        recent_videos = [
            {
                "title": v["snippet"]["title"],
                "published": v["snippet"]["publishedAt"][:10],
                "description": v["snippet"]["description"][:100]
            }
            for v in videos_resp.get("items", [])
        ]
        
        return {
            "channel_name": channel_title,
            "channel_id": channel_id,
            "subscribers": stats.get("subscriberCount", "hidden"),
            "total_videos": stats.get("videoCount", "N/A"),
            "total_views": stats.get("viewCount", "N/A"),
            "recent_videos": recent_videos
        }
    except Exception as e:
        return {"error": str(e)}


def scrape_google_maps(query: str, location: str, depth: int = 1, extract_emails: bool = False, extra_reviews: bool = False, max_retries: int = 2) -> dict:
    if not GOOGLE_MAPS_SCRAPER_AVAILABLE:
        return {"error": "Google Maps Scraper not available."}

    for attempt in range(max_retries + 1):
        temp_dir = None
        try:
            # Create a temporary directory that will be mounted into the container
            import tempfile
            temp_dir = tempfile.mkdtemp()
            input_file_path = os.path.join(temp_dir, "input.txt")
            
            with open(input_file_path, 'w', encoding='utf-8') as f:
                f.write(f"{query} in {location}\n")
            
            # Container will see the file at /input/input.txt
            cmd = [
                "docker", "run", "--rm", "-i",
                "-v", f"{temp_dir}:/input",   # mount the temp dir
                "gosom/google-maps-scraper",
                "-depth", str(depth),
                "-json",
                "-input", "/input/input.txt",
                "-results", "/dev/stdout"
            ]
            if extract_emails:
                cmd.append("-email")
            if extra_reviews:
                cmd.append("--extra-reviews")
            
            timeout_duration = 180 if attempt == 0 else 120
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_duration,
                encoding='utf-8',
                errors='replace'
            )
            
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            if result.returncode != 0:
                if attempt < max_retries:
                    print(f"  [!] Scraper failed (attempt {attempt+1}/{max_retries+1}), retrying...")
                    time.sleep(5)
                    continue
                return {"error": f"Docker command failed: {result.stderr}"}
            
            # Parse output (same as before)
            if result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                    return {"success": True, "data": data}
                except json.JSONDecodeError:
                    lines = result.stdout.strip().split('\n')
                    data = [json.loads(line) for line in lines if line.strip()]
                    return {"success": True, "data": data}
            else:
                return {"error": "No output from Google Maps Scraper"}
                
        except subprocess.TimeoutExpired:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
            if attempt < max_retries:
                print(f"  [!] Scraper timed out (attempt {attempt+1}/{max_retries+1}), retrying in 10s...")
                time.sleep(10)
                continue
            return {"error": f"Scraper timed out after {timeout_duration}s"}
        except Exception as e:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
            if attempt < max_retries:
                print(f"  [!] Scraper error: {e}, retrying...")
                time.sleep(5)
                continue
            return {"error": f"Scraper error: {str(e)}"}
    
    return {"error": "All retries exhausted"}
def google_maps_scraper_tool():
    """
    Returns a function that can be used as an agno tool for Google Maps scraping.
    This allows the scraper to be used directly by agents.
    """
    def scrape(query: str, location: str, depth: int = 1) -> str:
        """
        Scrape Google Maps for business data.
        
        Args:
            query: Search query (e.g., "restaurants")
            location: Geographic location (e.g., "Amsterdam")
            depth: Max scroll depth (default: 1)
        
        Returns:
            JSON string with scraped business data
        """
        result = scrape_google_maps(query, location, depth)
        if result.get("success"):
            return json.dumps(result["data"], indent=2)
        else:
            return json.dumps({"error": result.get("error")})
    
    return scrape
