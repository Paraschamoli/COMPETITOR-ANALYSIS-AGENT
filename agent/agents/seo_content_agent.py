#!/usr/bin/env python3
"""
SEO & Content Strategy Analyst Agent
Simplified version - fixes empty output issue
"""

from agno.agent import Agent
from ..models import agent_model
from ..tools import all_tools


def seo_content_agent() -> Agent:
    """Create and return the Local SEO & Content Strategy Analyst agent"""
    return Agent(
        name="Local SEO & Content Strategy Analyst",
        role="Analyze local search presence, Google Maps optimization, and local content marketing.",
        model=agent_model(max_tokens=6000),
        tools=all_tools(),
        instructions=[
            "IMPORTANT: You MUST produce actual output. DO NOT return empty responses.",
            "",
            "TASK: Analyze SEO and online presence for {company} and competitors in {location}.",
            "Business type: {domain}",
            "",
            "OUTPUT FORMAT - USE THESE EXACT HEADERS:",
            "",
            "### {company} - SEO & Digital Presence",
            "**Google Rating:** [X.X/5] | **Reviews:** [count]",
            "",
            "**Online Presence:**",
            "- [Website quality, reviews platforms, social media]",
            "",
            "**SEO Strengths:**",
            "- [What they do well online]",
            "",
            "---",
            "",
            "### [Competitor Name]",
            "**Google Rating:** [X.X/5] | **Reviews:** [count]",
            "",
            "**Online Presence:**",
            "- [Website quality, reviews platforms, social media]",
            "",
            "---",
            "",
            "REPEAT for EACH competitor from the provided list.",
            "",
            "SEARCH:",
            "1. Search '{company} Google reviews {location}'",
            "2. Search 'best {domain} {location} reviews'",
            "3. For each competitor: '[name] {location} Google reviews'",
            "",
            "If no data found, state 'No data available' - never leave empty.",
            "",
            "MUST INCLUDE: Analyze at least 6 competitors plus {company}",
        ],
        markdown=True,
    )