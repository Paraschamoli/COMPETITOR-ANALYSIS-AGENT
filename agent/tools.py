#!/usr/bin/env python3
"""
Tools and helpers for the Competitor Analysis Agent
"""

import asyncio
import subprocess
import json
import os
from agno.tools.tavily import TavilyTools
from agno.tools.serper import SerperTools
from agno.tools.firecrawl import FirecrawlTools
from .config import CRAWL4AI_AVAILABLE, YOUTUBE_AVAILABLE, YOUTUBE_API_KEY, GOOGLE_MAPS_SCRAPER_AVAILABLE


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


def scrape_google_maps(query: str, location: str, depth: int = 1, extract_emails: bool = False, extra_reviews: bool = False) -> dict:
    """
    Use Google Maps Scraper via Docker to extract business data.
    Returns comprehensive competitor data including reviews, ratings, coordinates.
    
    Args:
        query: Search query (e.g., "restaurants")
        location: Geographic location (e.g., "Amsterdam")
        depth: Max scroll depth in results (default: 1)
        extract_emails: Whether to extract emails from business websites
        extra_reviews: Collect extended reviews up to ~300
    
    Returns:
        Dict with scraped data or error message
    """
    if not GOOGLE_MAPS_SCRAPER_AVAILABLE:
        return {"error": "Google Maps Scraper not available. Docker must be installed and running."}
    
    try:
        # Build Docker command
        cmd = [
            "docker", "run", "--rm",
            "gosom/google-maps-scraper",
            "-depth", str(depth),
            "-json",  # Output JSON for easy parsing
            "-input", "/dev/stdin",
            "-results", "/dev/stdout"
        ]
        
        # Add optional flags
        if extract_emails:
            cmd.append("-email")
        if extra_reviews:
            cmd.append("--extra-reviews")
        
        # Prepare input
        input_data = f"{query} in {location}\n"
        
        # Run Docker command
        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout to prevent hanging
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode != 0:
            return {"error": f"Docker command failed: {result.stderr}"}
        
        # Parse JSON output
        if result.stdout.strip():
            try:
                data = json.loads(result.stdout)
                return {"success": True, "data": data}
            except json.JSONDecodeError:
                # Output might be multiple JSON lines
                lines = result.stdout.strip().split('\n')
                data = [json.loads(line) for line in lines if line.strip()]
                return {"success": True, "data": data}
        else:
            return {"error": "No output from Google Maps Scraper"}
            
    except subprocess.TimeoutExpired:
        return {"error": "Google Maps Scraper timed out after 30 seconds. Docker may be downloading the image or the command is hanging."}
    except FileNotFoundError:
        return {"error": "Docker not found. Please install Docker."}
    except Exception as e:
        return {"error": f"Google Maps Scraper error: {str(e)}"}


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
