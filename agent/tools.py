#!/usr/bin/env python3
"""
Tools and helpers for the Competitor Analysis Agent
"""

import asyncio
from agno.tools.tavily import TavilyTools
from agno.tools.serper import SerperTools
from agno.tools.firecrawl import FirecrawlTools
from .config import CRAWL4AI_AVAILABLE, YOUTUBE_AVAILABLE, YOUTUBE_API_KEY


def search_tools():
    """Serper only - avoiding Tavily rate limits"""
    tools = [TavilyTools(),SerperTools()]  # Only using Serper to avoid Tavily limits
    return tools


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
