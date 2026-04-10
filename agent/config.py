#!/usr/bin/env python3
"""
Configuration and utilities for the Competitor Analysis Agent
"""

import os
import subprocess
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model configuration
COORDINATOR_MODEL = "openai/gpt-4.1"   # or claude-sonnet-4-5, gemini/gemini-2.0-flash
AGENT_MODEL = "openai/gpt-4.1-mini"

# Optional: Crawl4AI (free, open-source alternative/supplement to Firecrawl)
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    print("⚠️  crawl4ai not installed. Using Firecrawl only. Run: pip install crawl4ai && crawl4ai-setup")

# Optional: Agent Reach (enhanced platform access)
try:
    def check_agent_reach():
        """Check if Agent Reach is available"""
        try:
            # First check if agent-reach command exists
            result = subprocess.run(['where', 'agent-reach'], 
                                  capture_output=True, text=True, 
                                  timeout=5, encoding='utf-8', errors='ignore')
            if result.returncode != 0:
                return False
            
            # If command exists, try a quick version check instead of doctor
            result = subprocess.run(['agent-reach', '--version'], 
                                  capture_output=True, text=True, 
                                  timeout=5, encoding='utf-8', errors='ignore')
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def agent_reach_search(platform: str, query: str) -> str:
        """Use Agent Reach for platform-specific search"""
        if not check_agent_reach():
            return f"Agent Reach not available for {platform} search"
        
        try:
            if platform.lower() == 'twitter':
                result = subprocess.run(['twitter', 'search', query, '-n', '10'], 
                                  capture_output=True, text=True, timeout=30,
                                  encoding='utf-8', errors='ignore')
            elif platform.lower() == 'reddit':
                result = subprocess.run(['rdt', 'search', query], 
                                  capture_output=True, text=True, timeout=30,
                                  encoding='utf-8', errors='ignore')
            elif platform.lower() == 'youtube':
                result = subprocess.run(['yt-dlp', '--dump-json', f'ytsearch10:{query}'], 
                                  capture_output=True, text=True, timeout=30,
                                  encoding='utf-8', errors='ignore')
            elif platform.lower() == 'github':
                result = subprocess.run(['gh', 'search', 'repos', query, '--limit', '10'], 
                                  capture_output=True, text=True, timeout=30,
                                  encoding='utf-8', errors='ignore')
            else:
                return f"Unsupported platform: {platform}"
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Agent Reach {platform} search failed: {result.stderr}"
        except subprocess.TimeoutExpired:
            return f"Agent Reach {platform} search timed out"
        except Exception as e:
            return f"Agent Reach {platform} error: {e}"
    
    AGENT_REACH_AVAILABLE = check_agent_reach()
    if AGENT_REACH_AVAILABLE:
        print("✅ Agent Reach available - enhanced platform access enabled")
    else:
        print("⚠️  Agent Reach not available. Install: https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md")
        
except ImportError:
    AGENT_REACH_AVAILABLE = False
    print("⚠️  Agent Reach integration disabled")

# Optional: YouTube Data API (free — 10,000 units/day)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
try:
    from googleapiclient.discovery import build as youtube_build
    YOUTUBE_AVAILABLE = bool(YOUTUBE_API_KEY)
except ImportError:
    YOUTUBE_AVAILABLE = False
    print("⚠️  google-api-python-client not installed. YouTube analysis will use search fallback.")

# Advanced Features Configuration
# Toggle advanced report sections (Methodology, Personas, Risk, etc.)
ENABLE_ADVANCED_SECTIONS = os.getenv("ENABLE_ADVANCED_SECTIONS", "true").lower() == "true"

# Toggle ASCII/text-based visual charts in reports
ENABLE_VISUAL_CHARTS = os.getenv("ENABLE_VISUAL_CHARTS", "true").lower() == "true"

# Data verification mode - strict mode rejects unverified data
STRICT_VERIFICATION = os.getenv("STRICT_VERIFICATION", "true").lower() == "true"
